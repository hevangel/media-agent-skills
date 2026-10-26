"""
Capture book pages from the Internet Archive BookReader using Playwright.

Given an archive.org details URL, this script:
  1. Opens the page in Chromium and waits for the BookReader to render
  2. Screenshots the book view, saving PNGs numbered from 0001.png
  3. Clicks the flip button (right/next by default, or left/previous with
     --direction left), tracking progress via the "Page - (n/total)" indicator
  4. Repeats until the end of the direction (the reader wraps around) or --max-pages
  5. Combines the PNGs into a single PDF in the output folder

Authentication: public books need none. Borrow-restricted books need a
logged-in session: the script logs in automatically with IA_USERNAME /
IA_PASSWORD from the workspace .env (caching cookies to a storage-state file),
or you can pass an existing --storage-state / --user-data-dir (see SKILL.md).

Usage:
    uv run python skills/internetarchive/scripts/capture_book_pages.py \
        "https://archive.org/details/<identifier>/mode/2up"
    uv run python skills/internetarchive/scripts/capture_book_pages.py \
        "https://archive.org/details/<identifier>/mode/2up" --max-pages 3 --headed
    uv run python skills/internetarchive/scripts/capture_book_pages.py \
        "https://archive.org/details/<identifier>/mode/2up" --pdf-only
    uv run python skills/internetarchive/scripts/capture_book_pages.py --login
"""

import argparse
import ipaddress
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import img2pdf
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STATE_PATH = WORKSPACE_ROOT / "temp" / "ia_storage_state.json"
LOGIN_URL = "https://archive.org/login"


class CaptureError(Exception):
    """Raised when the book page cannot be captured."""


def validate_archive_url(url: str) -> str:
    """Accept only https archive.org URLs; reject IP/localhost/private hosts."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise CaptureError(f"URL must be https: {url}")
    host = parsed.hostname or ""
    try:
        ipaddress.ip_address(host)
        raise CaptureError(f"IP-literal hosts are not allowed: {host}")
    except ValueError:
        pass  # not an IP literal, continue
    if host != "archive.org" and not host.endswith(".archive.org"):
        raise CaptureError(f"Only archive.org URLs are supported, got host: {host}")
    return url


def extract_identifier(url: str) -> str:
    """Pull the item identifier out of a /details/<identifier>/... URL."""
    match = re.search(r"/details/([^/?#]+)", url)
    if not match:
        raise CaptureError(f"Could not find item identifier in URL: {url}")
    identifier = match.group(1)
    if identifier in {".", ".."} or "\\" in identifier or ".." in identifier:
        raise CaptureError(f"Suspicious item identifier: {identifier}")
    return identifier


READER_STATE_JS = """
(() => {
    const out = { ready: false, index: null, numLeafs: null, mode: null };
    try {
        if (typeof br !== 'undefined' && br && br.book) {
            out.numLeafs = br.book.getNumLeafs();
            out.ready = !!document.querySelector('#BookReader') && out.numLeafs > 0;
            if (typeof br.currentIndex === 'function') out.index = br.currentIndex();
            out.mode = typeof br.mode === 'function' ? br.mode() : br.mode;
        }
    } catch (e) { /* reader not up yet */ }
    if (out.index === null) {
        const el = document.querySelector('.BRcurrentpage');
        if (el) {
            const m = el.textContent.match(/\\((\\d+)\\s*\\/\\s*(\\d+)\\)/);
            if (m) out.index = parseInt(m[1], 10) - 1;
        }
    }
    return JSON.stringify(out);
})()
"""

PAGES_LOADED_JS = """
(() => {
    const imgs = Array.from(document.querySelectorAll('img.BRpageimage'))
        .filter(i => {
            const r = i.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        });
    return JSON.stringify({
        count: imgs.length,
        loaded: imgs.every(i => i.complete && i.naturalWidth > 0),
    });
})()
"""

FLIP_JS = """
(dir) => {
    const cls = dir === 'left' ? 'book_flip_prev' : 'book_flip_next';
    const btn = document.querySelector(`button.${cls}:not(.hide)`)
        || document.querySelector(`button.${cls}`);
    if (btn) { btn.click(); return true; }
    return false;
}
"""

PAGE_LABEL_JS = """
(() => {
    const el = document.querySelector('.BRcurrentpage');
    if (!el) return null;
    const m = el.textContent.match(/\\((\\d+)\\s*\\/\\s*(\\d+)\\)/);
    return m ? m[1] + '/' + m[2] : el.textContent.trim().slice(0, 30);
})()
"""


def flip(page, direction: str) -> None:
    """Turn the page: click the flip button (left = previous, right = next),
    with keyboard and BookReader API fallbacks."""
    if page.evaluate(FLIP_JS, direction):
        return
    try:
        page.keyboard.press("ArrowLeft" if direction == "left" else "ArrowRight")
        return
    except Exception:
        pass
    api = "prev" if direction == "left" else "next"
    page.evaluate(
        f"(() => {{ if (typeof br !== 'undefined' && br) br.{api}(); }})()"
    )


def get_page_label(page) -> str:
    """Current page as shown by the reader's 'Page - (n/total)' indicator."""
    try:
        return page.evaluate(PAGE_LABEL_JS) or "?"
    except Exception:
        return "?"

PLACEHOLDER_JS = """
(() => {
    const imgs = Array.from(document.querySelectorAll('img.BRpageimage'))
        .filter(i => {
            const r = i.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        });
    return JSON.stringify({
        count: imgs.length,
        preview: imgs.some(i => i.src.includes('/static/preview')),
    });
})()
"""


def is_preview_placeholder(page) -> bool:
    """True when the visible spread is a 'Limited preview' placeholder image.

    Restricted books load fine without a loan, but pages outside the preview
    range render archive.org/bookreader/static/preview-*.png placeholders
    instead of real scans, so reader-load success alone proves nothing.
    """
    info = json.loads(page.evaluate(PLACEHOLDER_JS))
    return info["count"] > 0 and info["preview"]


def get_reader_state(page) -> dict:
    return json.loads(page.evaluate(READER_STATE_JS))


def get_index(page) -> int | None:
    return get_reader_state(page).get("index")


def wait_for_reader(page, timeout_ms: int) -> dict:
    """Wait until the BookReader is mounted with a non-empty book."""
    deadline = time.monotonic() + timeout_ms / 1000
    state = {}
    while time.monotonic() < deadline:
        state = get_reader_state(page)
        if state.get("ready"):
            return state
        if "account/login" in page.url:
            raise CaptureError(
                "Redirected to archive.org login. Run with --login to save a "
                "storage state, then pass --storage-state (or --user-data-dir)."
            )
        page.wait_for_timeout(500)
    raise CaptureError(
        "BookReader did not load in time. If this book is borrow-restricted, "
        "borrow it and provide a logged-in session (--storage-state or "
        "--user-data-dir); see the internetarchive SKILL.md."
    )


def wait_pages_settled(page, timeout_ms: int) -> None:
    """Wait until every visible page image has finished decoding."""
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        info = json.loads(page.evaluate(PAGES_LOADED_JS))
        if info["count"] > 0 and info["loaded"]:
            return
        page.wait_for_timeout(300)
    print("  warning: page images still loading, capturing anyway")


def wait_index_change(page, old_index, timeout_ms: int) -> int | None:
    """Wait for the leaf index to move; return the new index, or None on timeout."""
    if old_index is None:
        page.wait_for_timeout(2000)
        return None
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        index = get_index(page)
        if index is not None and index != old_index:
            return index
        page.wait_for_timeout(300)
    return None


def take_screenshot(page, path: Path, full_page: bool) -> None:
    if not full_page:
        container = page.locator(".BRcontainer")
        if container.count() == 1:
            container.screenshot(path=str(path))
            return
    page.screenshot(path=str(path))


def find_storage_state_path(args) -> Path | None:
    """Explicit --storage-state wins; otherwise reuse the cached default if present."""
    if args.storage_state:
        return Path(args.storage_state)
    if DEFAULT_STATE_PATH.exists():
        return DEFAULT_STATE_PATH
    return None


def is_logged_in(context) -> bool:
    """True when the archive.org logged-in-user cookie is set."""
    return any(c["name"] == "logged-in-user" for c in context.cookies("https://archive.org"))


def login_with_credentials(page, context, username: str, password: str,
                           timeout_ms: int) -> bool:
    """Fill and submit the archive.org login form; wait for the session cookie.

    The form renders inside a shadow DOM, so plain document.querySelectorAll
    cannot see it - Playwright locators pierce shadow roots. The password comes
    from the .env loaded in main(); it is never stored or logged. The session
    is cached to the fixed DEFAULT_STATE_PATH under the workspace temp dir.
    """
    print("Logging in to archive.org with credentials from .env ...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    page.locator("input[name=username]").fill(username)
    page.locator("input[name=password]").fill(password)
    remember = page.locator("input[name=remember]")
    if remember.count() == 1:
        try:
            remember.check()
        except Exception:
            pass  # optional checkbox; some variants of the form omit it
    # The submit button is a slotted-label shadow-DOM element that is hard to
    # target reliably; pressing Enter in the password field submits the form.
    page.locator("input[name=password]").press("Enter")

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if is_logged_in(context):
            DEFAULT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(DEFAULT_STATE_PATH))
            print(f"Login OK; cached session to {DEFAULT_STATE_PATH}")
            return True
        page.wait_for_timeout(500)
    print("Login did not succeed (wrong credentials or a CAPTCHA appeared).")
    return False


def attempt_borrow(page, identifier: str, timeout_ms: int) -> None:
    """Refresh the reader loan by visiting the details page and reloading it.

    archive.org/borrow/<id> is not a valid URL (404). For a logged-in user a
    details-page visit renews an expired 1-hour web reader loan, and the
    reload makes the reader re-render pages with the fresh loan cookies.
    """
    details_url = f"https://archive.org/details/{identifier}"
    print(f"Visiting {details_url} to refresh the loan ...")
    try:
        page.goto(details_url, timeout=timeout_ms)
        page.wait_for_timeout(5000)
        page.reload(wait_until="load")
        page.wait_for_timeout(3000)
    except PlaywrightTimeoutError:
        print("  loan refresh timed out, continuing anyway")


def open_reader(page, context, url: str, identifier: str, timeout_ms: int) -> dict:
    """Load the reader, logging in / borrowing when access is denied.

    Retry chain: direct load -> credential login + retry -> borrow + retry.
    """
    try:
        page.goto(url, timeout=timeout_ms)
        return wait_for_reader(page, timeout_ms)
    except CaptureError:
        username = os.environ.get("IA_USERNAME")
        password = os.environ.get("IA_PASSWORD")
        if not (username and password):
            raise
        if not is_logged_in(context):
            if not login_with_credentials(page, context, username, password, timeout_ms):
                raise
        print("Retrying the book page after login ...")
        page.goto(url, timeout=timeout_ms)
        try:
            return wait_for_reader(page, timeout_ms)
        except CaptureError:
            attempt_borrow(page, identifier, timeout_ms)
            page.goto(url, timeout=timeout_ms)
            return wait_for_reader(page, timeout_ms)


def ensure_full_access(page, context, identifier: str, url: str,
                       resume_index: int, mode, timeout_ms: int) -> None:
    """Upgrade a limited preview to full access, then resume at the same spread.

    Logs in with IA_USERNAME/IA_PASSWORD (unless already logged in), starts a
    1-hour reader loan via archive.org/borrow/<id>, and reopens the book at the
    spread where the preview wall was hit.
    """
    username = os.environ.get("IA_USERNAME")
    password = os.environ.get("IA_PASSWORD")
    if not (username and password):
        raise CaptureError(
            "This book shows a 'Limited preview' and needs a loan for full "
            "access. Set IA_USERNAME / IA_PASSWORD in the workspace .env, or "
            "borrow the book in a browser and run --login."
        )
    if not is_logged_in(context):
        if not login_with_credentials(page, context, username, password, timeout_ms):
            raise CaptureError("Login failed; cannot borrow the book.")
    attempt_borrow(page, identifier, timeout_ms)
    # In 2-up the #page/n<N> fragment names the right page of the spread, so
    # add 1 to the left-page index; in 1-up the fragment equals the index.
    n = resume_index + 1 if mode == 2 else resume_index
    resume_url = apply_start_index(url, n)
    print(f"Resuming at leaf {resume_index} after loan refresh ...")
    page.goto(resume_url, timeout=timeout_ms)
    wait_for_reader(page, timeout_ms)
    # Reload once so the spread re-renders with the loan cookies set above.
    page.reload(wait_until="load")
    wait_for_reader(page, timeout_ms)


def combine_to_pdf(png_paths: list[Path], output_dir: Path, identifier: str) -> Path:
    """Merge screenshots into <output_dir>/<identifier>.pdf (lossless img2pdf)."""
    if ".." in output_dir.parts:
        raise CaptureError(f"Output directory must not contain '..': {output_dir}")
    pdf_path = output_dir / f"{identifier}.pdf"
    print(f"Combining {len(png_paths)} screenshot(s) into {pdf_path.name} ...")
    pdf_path.write_bytes(img2pdf.convert([str(p) for p in png_paths]))
    return pdf_path


def do_login() -> None:
    """Open a visible browser, let the user log in, then save the storage state."""
    print(f"Opening {LOGIN_URL} - log in inside the browser window.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(LOGIN_URL)
        input("After logging in (and borrowing the book if needed), press Enter here... ")
        DEFAULT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(DEFAULT_STATE_PATH))
        browser.close()
    print(f"Saved login state to {DEFAULT_STATE_PATH}")


def apply_start_index(url: str, start_index: int) -> str:
    """Rewrite the URL so the reader opens at #page/n<start_index>.

    The details page drops a /page/n<N>/ path segment on load, but honors the
    hash fragment form #page/n<N>/mode/<mode> (N is 0-based; in 2-up mode N is
    the right page of the spread).
    """
    mode_match = re.search(r"/mode/(\d+up)", url)
    mode = mode_match.group(1) if mode_match else "2up"
    base = url.split("#", 1)[0]
    base = re.sub(r"/page/n\d+", "", base)
    base = re.sub(r"/mode/\d+up/?", "/", base)
    return f"{base.rstrip('/')}#page/n{start_index}/mode/{mode}"


def capture(url: str, args) -> None:
    validate_archive_url(url)
    identifier = extract_identifier(url)
    output_dir = Path(args.output_dir) if args.output_dir else (
        WORKSPACE_ROOT / "temp" / "internetarchive" / identifier
    )
    if ".." in output_dir.parts:
        raise CaptureError(f"Output directory must not contain '..': {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        width, height = (int(v) for v in args.viewport.lower().split("x"))
    except ValueError:
        raise CaptureError(f"Invalid viewport (expect WIDTHxHEIGHT): {args.viewport}")

    timeout_ms = args.timeout * 1000
    state_path = find_storage_state_path(args)
    print(f"Capturing {url}")
    print(f"Output: {output_dir}")
    if state_path:
        print(f"Login session: {state_path}")

    with sync_playwright() as p:
        if args.user_data_dir:
            context = p.chromium.launch_persistent_context(
                args.user_data_dir,
                headless=not args.headed,
                viewport={"width": width, "height": height},
            )
        else:
            browser = p.chromium.launch(headless=not args.headed)
            context = browser.new_context(
                viewport={"width": width, "height": height},
                storage_state=str(state_path) if state_path else None,
            )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            if args.start_index is not None:
                url = apply_start_index(url, args.start_index)
                print(f"Starting at leaf {args.start_index}")
            state = open_reader(page, context, url, identifier, timeout_ms)
            num_leafs = state["numLeafs"]
            mode = state.get("mode")
            print(f"Reader ready: {num_leafs} leaves, mode={mode}")

            shot_num = 1
            shots_taken = 0
            access_upgraded = False
            start_time = time.monotonic()
            while shot_num <= args.max_pages:
                wait_pages_settled(page, timeout_ms)
                page.wait_for_timeout(int(args.delay * 1000))

                if is_preview_placeholder(page):
                    if access_upgraded:
                        raise CaptureError(
                            "Pages still show 'Limited preview' after login and "
                            "borrowing (loan limit reached or borrow failed); "
                            "stopping to avoid placeholder screenshots."
                        )
                    access_upgraded = True
                    wall_index = get_index(page) or 0
                    print(f"Limited preview wall at leaf {wall_index}; "
                          "logging in and borrowing the book ...")
                    ensure_full_access(page, context, identifier, url,
                                       wall_index, mode, timeout_ms)
                    continue

                out_path = output_dir / f"{shot_num:04d}.png"
                take_screenshot(page, out_path, args.full_page)
                shots_taken += 1
                print(f"  [{shot_num:04d}] Page {get_page_label(page)} "
                      f"(leaf {get_index(page)}) -> {out_path.name}")

                index_before = get_index(page)
                flip(page, args.direction)
                new_index = wait_index_change(page, index_before, timeout_ms)
                if index_before is None:
                    pass  # no index info; rely on --max-pages
                elif new_index is None:
                    print("Page index stopped changing; stopping.")
                    break
                elif args.direction == "left":
                    # Backward flips wrap to the end at the first page, so a
                    # non-decreasing index means the front cover was reached.
                    if new_index >= index_before:
                        print("Reached the first page.")
                        break
                elif new_index <= index_before:
                    # Forward flips wrap to the start at the last page.
                    print("Reached the last page.")
                    break
                shot_num += 1

            elapsed = time.monotonic() - start_time
            print(f"Done: {shots_taken} screenshot(s) in {elapsed:.0f}s -> {output_dir}")
            if not args.no_pdf and shots_taken > 0:
                pngs = sorted(output_dir.glob("????.png"))
                pdf_path = combine_to_pdf(pngs, output_dir, identifier)
                print(f"PDF: {pdf_path}")
        finally:
            if args.user_data_dir:
                context.close()
            else:
                context.close()
                browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot archive.org BookReader pages by flipping to the end"
    )
    parser.add_argument("url", nargs="?", help="archive.org details URL of the book")
    parser.add_argument("--output-dir", "-o", default=None, help="Output folder for PNGs")
    parser.add_argument("--max-pages", "-m", type=int, default=2000,
                        help="Safety cap on number of screenshots")
    parser.add_argument("--start-index", type=int, default=None,
                        help="0-based leaf index to start from")
    parser.add_argument("--direction", choices=["right", "left"], default="right",
                        help="right: flip forward to the last page (default); "
                             "left: click the flip-left button backward to the first page")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Extra settle seconds after each flip")
    parser.add_argument("--viewport", default="1600x1200",
                        help="Browser viewport, WIDTHxHEIGHT")
    parser.add_argument("--full-page", action="store_true",
                        help="Screenshot the whole viewport instead of the book area")
    parser.add_argument("--headed", action="store_true", help="Show the browser")
    parser.add_argument("--storage-state", default=None,
                        help="Playwright storage state with archive.org cookies")
    parser.add_argument("--user-data-dir", default=None,
                        help="Persistent Chrome profile directory (keeps login)")
    parser.add_argument("--login", action="store_true",
                        help="Interactive login helper; saves storage state and exits")
    parser.add_argument("--no-pdf", action="store_true",
                        help="Skip combining the PNGs into a PDF after capture")
    parser.add_argument("--pdf-only", action="store_true",
                        help="Skip capture; recombine existing PNGs in the output folder")
    parser.add_argument("--timeout", type=int, default=90,
                        help="Load/readiness timeout in seconds")
    args = parser.parse_args()

    load_dotenv(WORKSPACE_ROOT / ".env")

    try:
        if args.login:
            do_login()
            return
        if not args.url:
            parser.error("a book URL is required (unless using --login or --pdf-only)")
        identifier = extract_identifier(validate_archive_url(args.url))
        output_dir = Path(args.output_dir) if args.output_dir else (
            WORKSPACE_ROOT / "temp" / "internetarchive" / identifier
        )
        if args.pdf_only:
            if ".." in output_dir.parts:
                raise CaptureError(f"Output directory must not contain '..': {output_dir}")
            pngs = sorted(output_dir.glob("????.png"))
            if not pngs:
                raise CaptureError(f"No ?????.png screenshots found in {output_dir}")
            pdf_path = combine_to_pdf(pngs, output_dir, identifier)
            print(f"PDF: {pdf_path}")
            return
        capture(args.url, args)
    except CaptureError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    except PlaywrightTimeoutError as exc:
        print(f"Error: page timed out - {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

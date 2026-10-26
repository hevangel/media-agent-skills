---
name: internetarchive
description: "Search books on the Internet Archive (archive.org) and capture BookReader pages to PNG/PDF with Playwright. Use when the user needs to find archive.org books, take page screenshots, or build a PDF of a book, including borrow-restricted books with an active loan."
license: MIT
compatibility: Requires Python 3.13+, uv, playwright (chromium installed), requests, and img2pdf
---

# Internet Archive Book Page Capture

Given an archive.org book link (e.g. `https://archive.org/details/<identifier>/mode/2up`),
drive the on-page BookReader with Playwright: screenshot the book view, click the
flip button so the page turns left to the next spread, and repeat until the last
page. Screenshots are saved as `0001.png`, `0002.png`, ... in the output folder,
then combined into `<identifier>.pdf` (lossless, via img2pdf).

Page images in the BookReader are rendered from `blob:` URLs (DRM/loan protected),
so screenshotting the rendered reader is the reliable way to capture them; direct
image downloads do not work for access-restricted items.

## Configuration

Archive.org credentials live in the workspace `.env` (see `.env.example`); the
script loads them automatically and logs in only when a book needs it:

```env
IA_USERNAME=your_archive_org_email
IA_PASSWORD=your_archive_org_password
```

After the first successful login the session is cached to
`temp/ia_storage_state.json` and reused, so logins are rare.

## Reference

- Code Snippets: `scripts/`
- Playwright Python docs: https://playwright.dev/python/docs/intro
- Internet Archive BookReader: https://github.com/internetarchive/bookreader

## Available Scripts

| Script | Purpose |
|--------|---------|
| `search_books.py` | Find books via the advancedsearch API (filters: title/creator/subject/collection/year) |
| `capture_book_pages.py` | Screenshot every page/spread of an archive.org book by flipping through the BookReader |

## Searching for Books

`search_books.py` wraps the [advancedsearch API](https://archive.org/advancedsearch.php)
so finding a book is one command instead of driving the archive.org UI by hand:

```bash
# free text + author
uv run python skills/internetarchive/scripts/search_books.py "computer architecture" --creator hennessy

# title + year range (public-domain era)
uv run python skills/internetarchive/scripts/search_books.py --title "alice in wonderland" --year 1865-1930

# identifiers only, for piping straight into capture
uv run python skills/internetarchive/scripts/search_books.py --creator "lewis carroll" --ids
```

Each result shows the identifier, title, creator, year, lending availability
(`available_to_borrow` / `available_to_browse` / `available_to_waitlist`), and
download count. `--mediatype` (default `texts`), `--collection`, `--subject`,
`--rows` (max 100), `--page`, and `--sort` refine the search; the positional
query accepts the API's Lucene syntax (e.g. `title:foo AND !collection:bar`).

Then capture the chosen identifier:

```bash
uv run python skills/internetarchive/scripts/capture_book_pages.py \
    "https://archive.org/details/<identifier>/mode/2up"
```

## Usage

Capture a book (public books need no login; restricted books log in with the
`.env` credentials, borrow if needed, then capture):

```bash
uv run python skills/internetarchive/scripts/capture_book_pages.py \
    "https://archive.org/details/lccn_1558800698/mode/2up"
```

Result: `temp/internetarchive/<identifier>/` with `0001.png ... NNNN.png` plus
`<identifier>.pdf`.

Recombine existing PNGs into the PDF without recapturing:

```bash
uv run python skills/internetarchive/scripts/capture_book_pages.py \
    "https://archive.org/details/<identifier>/mode/2up" --pdf-only
```

One-time interactive login fallback (opens a visible browser for CAPTCHAs etc.;
saves the session to `temp/ia_storage_state.json` and exits):

```bash
uv run python skills/internetarchive/scripts/capture_book_pages.py --login
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output-dir DIR` | `temp/internetarchive/<identifier>` | Where PNGs/PDF are written |
| `--max-pages N` | 2000 | Safety cap on number of screenshots |
| `--start-index N` | reader's current page | 0-based leaf index to start from (2-up: right page of the spread) |
| `--direction {right,left}` | right | right flips forward to the last page; left clicks the flip-left button backward to the first page |
| `--delay SECONDS` | 2.0 | Extra settle time after each flip |
| `--viewport WIDTHxHEIGHT` | 1600x1200 | Browser viewport (bigger = sharper pages) |
| `--full-page` | off | Screenshot the whole viewport instead of the book area |
| `--no-pdf` | off | Skip combining the PNGs into a PDF after capture |
| `--pdf-only` | off | Skip capture; recombine existing PNGs in the output folder |
| `--headed` | off | Show the browser while capturing |
| `--storage-state FILE` | auto (`temp/ia_storage_state.json` if present) | Login session to reuse |
| `--user-data-dir DIR` | none | Persistent Chrome profile (keeps login) |
| `--login` | - | Interactive login helper; saves the storage state |
| `--timeout SECONDS` | 90 | Page load / reader readiness timeout |

## How It Works

Verified against the current BookReader on `archive.org/details` pages:

- Reader readiness: `#BookReader` container and the `window.br` object exist
- Flip buttons: `button.BRicon.book_flip_next` (page turns left/forward) and
  `button.BRicon.book_flip_prev` (backward, used by `--direction left`). They
  are zero-size until hovered, so the script clicks them via a DOM `click()`,
  with arrow-keypresses and `br.next()`/`br.prev()` as fallbacks
- Progress: each shot logs the reader's `Page - (n/total)` indicator (e.g.
  `Page 15/791`) plus the 0-based leaf index; `br.currentIndex()` and
  `br.book.getNumLeafs()` drive the loop logic
- Settle wait: every visible `img.BRpageimage` must finish decoding
  (`complete && naturalWidth > 0`) before a screenshot is taken
- Limited preview: placeholder spreads are detected by their
  `/bookreader/static/preview-*.png` image source before each screenshot
- Last page: after the final spread the reader wraps around (forward flips
  wrap to the start, backward flips wrap to the end), so the loop stops when
  the leaf index fails to advance in the capture direction
- First leaf quirk: at the very front the cover often displays as a lone
  right-hand page (`Page 0/791`) before the first two-page spread

In `mode/2up` each screenshot contains a two-page spread (one flip = one
screenshot); in `mode/1up` each screenshot is a single page. The mode is taken
from the URL.

`--start-index N` opens the reader at `#page/n<N>/mode/<mode>` (hash form): a
`/page/n<N>/` **path** segment is dropped by the site on load, but the hash
fragment is honored. `N` is the 0-based leaf; in 2-up mode it is the right page
of the starting spread.

## Borrow-Restricted Books

Books in the lending library (`inlibrary` / `printdisabled` collections) load
their reader even without a loan, but pages outside a small free preview render
"Limited preview / Some pages are omitted" placeholders - so reader-load success
alone proves nothing. The script handles the whole chain:

1. Opens the book with the cached session (`temp/ia_storage_state.json`) if present
2. Before each screenshot it checks the visible spread: placeholder pages load
   from `archive.org/bookreader/static/preview-*.png`, real pages from `blob:`
   URLs, so the wall is detectable wherever it appears in the book
3. On hitting the wall it logs in with `IA_USERNAME` / `IA_PASSWORD` from `.env`
   (the login form renders inside a shadow DOM; it is filled by name and
   submitted with Enter), visits the details page and reloads it - for a
   logged-in user this (re)starts the 1-hour web reader loan - then resumes at
   the same spread with a fresh render
4. If placeholders persist after that, it stops with a clear error instead of
   saving placeholder screenshots

Notes:

- The web reader grants access through the `logged-in-user` and
  `loan-<identifier>` / `br-loan-<identifier>` cookies
- 1-hour reader loans auto-renew while in use; a book that was never borrowed
  may need one manual borrow (in a browser, then `--login`) before automation
  can refresh it
- A CAPTCHA at login can block automated sign-in - fall back to `--login`
- `--user-data-dir temp/internetarchive/profile` is an alternative that keeps
  the login in a persistent Chrome profile

## PDF Output

After capture (and with `--pdf-only`), the PNGs are merged into
`<output_dir>/<identifier>.pdf` with [img2pdf](https://pypi.org/project/img2pdf/)
- pages embed the original PNG data losslessly, one PDF page per screenshot
(two book pages per screenshot in 2-up mode). A 791-leaf book is ~400 PDF pages
and roughly 45-50 MB.

## Notes

- Only `https://archive.org` / `*.archive.org` URLs are accepted.
- Credentials are read only from `.env` (`IA_USERNAME` / `IA_PASSWORD`); they are
  never logged, committed, or written anywhere except the browser session.
- Output goes to `$WORKSPACE_PATH/temp/internetarchive/` by default; move final
  captures elsewhere afterwards.
- Keep `--delay` >= 1s: flipping too fast can capture a half-rendered page or
  trip rate limiting.
- A 791-page book in 2up mode is ~400 screenshots and can take 20+ minutes;
  use `--max-pages` for a quick test run first, then `--pdf-only` for the PDF.

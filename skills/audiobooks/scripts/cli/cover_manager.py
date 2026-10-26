"""
Audiobook Cover Manager CLI

Scans the audiobook library for missing covers, lists them, downloads cover
images, and embeds them into audio files.

Usage:
    uv run python skills/audiobooks/scripts/cli/cover_manager.py scan --report
    uv run python skills/audiobooks/scripts/cli/cover_manager.py list --by-author
    uv run python skills/audiobooks/scripts/cli/cover_manager.py process -i <INDEX> -u "<IMAGE_URL>"
    uv run python skills/audiobooks/scripts/cli/cover_manager.py embed -c cover.jpg -a "<AUDIOBOOK_DIR>"
"""

import argparse
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from core.scanner import AudiobookScanner
from core.downloader import CoverDownloader
from core.embedder import CoverEmbedder
from utils.image_handler import ImageHandler


def resolve_root(args_root: str | None) -> str:
    """Resolve the audiobook library root from args or AUDIOBOOKS_PATH."""
    root = args_root or os.getenv("AUDIOBOOKS_PATH")
    if not root:
        print("Error: library root not set. Pass --root or set AUDIOBOOKS_PATH in .env.")
        sys.exit(1)
    if not Path(root).is_dir():
        print(f"Error: library root does not exist: {root}")
        sys.exit(1)
    return root


def build_scanner(args_root: str | None) -> AudiobookScanner:
    scanner = AudiobookScanner(resolve_root(args_root))
    print(f"Scanning {scanner.audiobooks_root} ...")
    scanner.scan_audiobooks()
    return scanner


def sorted_missing(scanner: AudiobookScanner):
    """Missing-cover books in a stable order so list/process indices agree."""
    return sorted(
        scanner.get_missing_covers(),
        key=lambda ab: (ab.author.lower(), ab.title.lower()),
    )


def cmd_scan(args) -> None:
    scanner = build_scanner(args.root)

    out_path = Path(args.output) if args.output else PROJECT_ROOT / "temp" / "audiobook_scan_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scanner.save_scan_results(str(out_path))

    if args.report:
        report = scanner.generate_report()
        report_path = PROJECT_ROOT / "temp" / "audiobook_cover_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"Report saved to {report_path}")


def cmd_list(args) -> None:
    scanner = build_scanner(args.root)
    missing = sorted_missing(scanner)

    if not missing:
        print("All audiobooks have covers. Nothing to do.")
        return

    print(f"\n{len(missing)} audiobook(s) missing covers (use index with 'process -i <INDEX>'):\n")

    if args.by_author:
        by_author: dict[str, list] = {}
        for idx, book in enumerate(missing):
            by_author.setdefault(book.author, []).append((idx, book))
        for author in sorted(by_author):
            print(f"{author}:")
            for idx, book in by_author[author]:
                print(f"  [{idx}] {book.title}  ({len(book.audio_files)} audio files)")
                print(f"       {book.path}")
    else:
        for idx, book in enumerate(missing):
            print(f"[{idx}] {book.author} - {book.title}  ({len(book.audio_files)} audio files)")
            print(f"     {book.path}")


def cmd_process(args) -> None:
    scanner = build_scanner(args.root)
    missing = sorted_missing(scanner)

    if not (0 <= args.index < len(missing)):
        print(f"Error: index {args.index} out of range. Run 'list' first; valid range is 0..{len(missing) - 1}.")
        sys.exit(1)

    book = missing[args.index]
    book_dir = Path(book.path)
    print(f"\nProcessing [{args.index}]: {book.author} - {book.title}")
    print(f"  Directory: {book_dir}")

    cover_path = book_dir / "cover.jpg"

    downloader = CoverDownloader()
    result = downloader.download_from_url(args.url, str(cover_path))
    if not result.success:
        print(f"  Download failed: {result.error}")
        sys.exit(1)
    print(f"  Saved cover ({result.size_kb:.0f} KB): {cover_path}")

    converted = ImageHandler.ensure_jpg_format(str(cover_path))
    if converted and converted != str(cover_path):
        print(f"  Converted to JPEG: {converted}")

    embedder = CoverEmbedder()
    count = embedder.embed_cover_in_audiobook(str(book_dir), str(cover_path))
    if count == 0:
        print("  Warning: cover saved but no audio files were embedded.")
        sys.exit(1)
    print(f"  Done. Embedded cover art into {count} file(s).")


def cmd_embed(args) -> None:
    cover = Path(args.cover)
    book_dir = Path(args.audiobook)

    if not cover.is_file():
        print(f"Error: cover image not found: {cover}")
        sys.exit(1)
    if not book_dir.is_dir():
        print(f"Error: audiobook directory not found: {book_dir}")
        sys.exit(1)

    print(f"Embedding {cover.name} into audio files in {book_dir} ...")
    embedder = CoverEmbedder()
    count = embedder.embed_cover_in_audiobook(str(book_dir), str(cover))
    if count == 0:
        print("No audio files were embedded (none found or mutagen unavailable).")
        sys.exit(1)
    print(f"Done. Embedded cover art into {count} file(s).")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cover_manager",
        description="Scan audiobook library, fix missing covers, and embed cover art.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Scan the library and save results to JSON")
    p_scan.add_argument("--root", help="Audiobook library root (defaults to $AUDIOBOOKS_PATH)")
    p_scan.add_argument("--output", help="Path for scan results JSON (defaults to temp/audiobook_scan_results.json)")
    p_scan.add_argument("--report", action="store_true", help="Also print and save a markdown summary report")
    p_scan.set_defaults(func=cmd_scan)

    p_list = sub.add_parser("list", help="List audiobooks missing covers")
    p_list.add_argument("--root", help="Audiobook library root (defaults to $AUDIOBOOKS_PATH)")
    p_list.add_argument("--by-author", action="store_true", help="Group the listing by author")
    p_list.set_defaults(func=cmd_list)

    p_proc = sub.add_parser("process", help="Download a cover URL for a listed book and embed it")
    p_proc.add_argument("-i", "--index", type=int, required=True, help="Index from 'list' output")
    p_proc.add_argument("-u", "--url", required=True, help="Direct URL of the cover image")
    p_proc.add_argument("--root", help="Audiobook library root (defaults to $AUDIOBOOKS_PATH)")
    p_proc.set_defaults(func=cmd_process)

    p_embed = sub.add_parser("embed", help="Embed an existing cover image into an audiobook directory")
    p_embed.add_argument("-c", "--cover", required=True, help="Path to the cover image")
    p_embed.add_argument("-a", "--audiobook", required=True, help="Path to the audiobook directory")
    p_embed.set_defaults(func=cmd_embed)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

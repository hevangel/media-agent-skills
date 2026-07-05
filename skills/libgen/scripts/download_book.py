"""
Print LibGen download URLs and manual steps for a book MD5 hash.

For automated downloads use `playwright_download.py`, or drive the browser with
Webwright (install via the `microsoft/Webwright` agent plugin — see `scripts/README.md`)
and fall back to playwright-cli (@playwright/cli); this script only prints where to go and what to click.

Usage:
    uv run download_book.py <md5_hash> --output "path/to/output.epub"
    
Example:
    uv run download_book.py 0e5d19a33afebc900650bb582ad4df6a --output "temp/book.epub"
"""
import argparse
import os
import sys
from pathlib import Path


def get_download_url(md5: str) -> str:
    """
    Get the libgen.li ads page URL for a given MD5 hash.
    
    Args:
        md5: MD5 hash of the book
        
    Returns:
        URL to the libgen.li ads page
    """
    return f"https://libgen.li/ads.php?md5={md5}"


def get_annas_archive_url(md5: str) -> str:
    """
    Get the Anna's Archive URL for a given MD5 hash.
    
    Args:
        md5: MD5 hash of the book
        
    Returns:
        URL to the Anna's Archive page
    """
    return f"https://en.annas-archive.org/md5/{md5}"


def print_manual_download_instructions(md5: str) -> None:
    """
    Print instructions for manual download when automation fails.
    
    Args:
        md5: MD5 hash of the book
    """
    print("\n" + "=" * 60)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("=" * 60)
    print("\nAutomatic download requires browser automation (playwright_download.py, Webwright plugin, or playwright-cli).")
    print("To download manually, visit one of these URLs:\n")
    print(f"  1. {get_download_url(md5)}")
    print(f"     → Click the 'GET' button at the top\n")
    print(f"  2. {get_annas_archive_url(md5)}")
    print(f"     → Scroll down and click 'Libgen.li' link\n")
    print("If downloads fail, try using a VPN.")
    print("=" * 60)


def search_and_get_md5(title: str, author: str | None = None, format: str = "epub") -> str | None:
    """
    Search for a book and return its MD5 hash.
    
    Args:
        title: Book title to search for
        author: Author name to filter by (optional)
        format: Preferred format (default: epub)
        
    Returns:
        MD5 hash of the first matching result, or None if not found
    """
    from search_books import search_books
    
    results = search_books(title, author, format, limit=1)
    if results:
        return results[0].md5
    
    # Fallback: try without format filter
    results = search_books(title, author, limit=1)
    if results:
        return results[0].md5
    
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a book from Library Genesis",
        epilog="Note: For reliable downloads, use the Webwright plugin (microsoft/Webwright), playwright-cli (@playwright/cli), or playwright_download.py."
    )
    parser.add_argument("md5", help="MD5 hash of the book to download")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    # Just print download instructions: browser automation belongs in
    # playwright_download.py or an agent using Webwright / playwright-cli, not this script.
    print(f"Book MD5: {args.md5}")
    print_manual_download_instructions(args.md5)
    
    if args.output:
        print(f"\nRequested output path: {args.output}")
        print("After downloading manually, move the file to this location.")

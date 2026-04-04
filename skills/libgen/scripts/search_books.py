"""
Search for books on Library Genesis.

Usage:
    uv run search_books.py "Book Title" --author "Author Name" --format epub
"""
import argparse
from libgen_api_enhanced import LibgenSearch


def search_books(
    title: str,
    author: str | None = None,
    format: str | None = None,
    limit: int = 10
) -> list:
    """
    Search for books on Library Genesis.
    
    Args:
        title: Book title to search for
        author: Filter by author name (optional)
        format: Filter by file format - epub, pdf, mobi, etc. (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of Book objects matching the search criteria
    """
    search = LibgenSearch()
    results = search.search_title(title)
    
    filtered = results
    
    # Filter by author if specified
    if author:
        filtered = [r for r in filtered if author.lower() in r.author.lower()]
    
    # Filter by format if specified
    if format:
        filtered = [r for r in filtered if r.extension.lower() == format.lower()]
    
    return filtered[:limit]


def print_results(results: list) -> None:
    """Print search results in a formatted way."""
    if not results:
        print("No results found.")
        return
    
    print(f"\nFound {len(results)} results:")
    print("-" * 80)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.title}")
        print(f"   Author: {r.author}")
        print(f"   Format: {r.extension.upper()} | Size: {r.size}")
        print(f"   MD5: {r.md5}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for books on Library Genesis")
    parser.add_argument("title", help="Book title to search for")
    parser.add_argument("--author", "-a", help="Filter by author name")
    parser.add_argument("--format", "-f", help="Filter by format (epub, pdf, mobi)")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max results (default: 10)")
    
    args = parser.parse_args()
    
    results = search_books(args.title, args.author, args.format, args.limit)
    print_results(results)

"""
Search for media items on the Plex server.
Supports searching by query, content type, and within a specific library.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def search_media(query, content_type=None, library_name=None, limit=20):
    """
    Search for media items by query string.

    Args:
        query (str): Search query string.
        content_type (str, optional): Filter by type (e.g. 'movie', 'show', 'episode',
                                      'artist', 'album', 'track').
        library_name (str, optional): Restrict search to a specific library.
        limit (int): Maximum number of results.

    Returns:
        list: A list of matching item dicts.
    """
    plex = get_plex_client()
    print(f"Searching for '{query}' (type={content_type}, library={library_name}, limit={limit})...")

    if library_name:
        section = plex.library.section(library_name)
        if content_type:
            items = section.search(query=query, libtype=content_type, maxresults=limit)
        else:
            items = section.search(query=query, maxresults=limit)
    else:
        items = plex.search(query, limit=limit)

    print(f"Found {len(items)} results.")
    results = []
    for item in items:
        entry = {
            "title": item.title,
            "type": item.type,
            "ratingKey": item.ratingKey,
            "year": getattr(item, "year", None),
            "summary": getattr(item, "summary", "")[:200],
            "addedAt": str(getattr(item, "addedAt", "N/A")),
        }
        # Add parent info for episodes/tracks
        if hasattr(item, "grandparentTitle") and item.grandparentTitle:
            entry["show"] = item.grandparentTitle
        if hasattr(item, "parentTitle") and item.parentTitle:
            entry["season"] = item.parentTitle
        results.append(entry)

    return results


def display_results(items):
    """Pretty print search results."""
    for i, item in enumerate(items, 1):
        title = item.get("title", "Unknown")
        item_type = item.get("type", "Unknown")
        year = item.get("year", "N/A")
        rating_key = item.get("ratingKey", "N/A")
        show = item.get("show", "")
        prefix = f"{show} - " if show else ""
        print(f"  [{i}] {prefix}{title} ({year}) - Type: {item_type} - ID: {rating_key}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_media.py <search_query> [content_type] [library_name]")
        print("  content_type: movie, show, episode, artist, album, track")
        sys.exit(1)

    search_query = sys.argv[1]
    ctype = sys.argv[2] if len(sys.argv) > 2 else None
    lib = sys.argv[3] if len(sys.argv) > 3 else None

    results = search_media(search_query, content_type=ctype, library_name=lib)
    display_results(results)

    # Save results to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "plex_search_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

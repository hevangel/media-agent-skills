"""
Get all items from a specific Plex library.
Supports filtering by media type (movie, show, episode, artist, album, track).
"""

import json
import sys
from pathlib import Path

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def get_library_items(library_name, libtype=None, limit=100):
    """
    Get items from a specific library section.

    Args:
        library_name (str): The library section name (e.g. 'Movies', 'TV Shows').
        libtype (str, optional): Filter by item type (e.g. 'movie', 'show', 'episode',
                                 'artist', 'album', 'track').
        limit (int): Maximum number of items to return.

    Returns:
        list: A list of item dicts.
    """
    plex = get_plex_client()
    print(f"Fetching items from library '{library_name}' (type={libtype}, limit={limit})...")

    section = plex.library.section(library_name)

    if libtype:
        items = section.search(libtype=libtype, maxresults=limit)
    else:
        items = section.all()[:limit]

    print(f"Retrieved {len(items)} items.")
    results = []
    for item in items:
        entry = {
            "title": item.title,
            "type": item.type,
            "ratingKey": item.ratingKey,
            "year": getattr(item, "year", None),
            "addedAt": str(getattr(item, "addedAt", "N/A")),
            "rating": getattr(item, "rating", None),
        }
        results.append(entry)

    return results


def display_items(items):
    """Pretty print item summaries."""
    for i, item in enumerate(items, 1):
        title = item.get("title", "Unknown")
        item_type = item.get("type", "Unknown")
        year = item.get("year", "N/A")
        rating_key = item.get("ratingKey", "N/A")
        print(f"  [{i}] {title} ({year}) - Type: {item_type} - ID: {rating_key}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_library_items.py <library_name> [libtype] [limit]")
        print("  libtype: movie, show, episode, artist, album, track, etc.")
        print("\nRun list_libraries.py first to find library names.")
        sys.exit(1)

    lib_name = sys.argv[1]
    media = sys.argv[2] if len(sys.argv) > 2 else None
    max_items = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    items = get_library_items(lib_name, libtype=media, limit=max_items)
    display_items(items)

    # Save results to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "plex_library_items.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

"""
Get recently added items from the Plex server.
Supports filtering by library name.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def get_recently_added(library_name=None, limit=20):
    """
    Get recently added items.

    Args:
        library_name (str, optional): Restrict to a specific library.
        limit (int): Maximum number of items to return.

    Returns:
        list: A list of recently added item dicts.
    """
    plex = get_plex_client()
    print(f"Fetching recently added items (library={library_name}, limit={limit})...")

    if library_name:
        section = plex.library.section(library_name)
        items = section.recentlyAdded(maxresults=limit)
    else:
        items = plex.library.recentlyAdded()[:limit]

    print(f"Retrieved {len(items)} recently added items.")

    results = []
    for item in items:
        entry = {
            "title": item.title,
            "type": item.type,
            "ratingKey": item.ratingKey,
            "year": getattr(item, "year", None),
            "addedAt": str(getattr(item, "addedAt", "N/A")),
        }
        # Add parent info for episodes/tracks
        if hasattr(item, "grandparentTitle") and item.grandparentTitle:
            entry["show"] = item.grandparentTitle
        if hasattr(item, "parentTitle") and item.parentTitle:
            entry["season"] = item.parentTitle
        results.append(entry)

    return results


def display_items(items):
    """Pretty print recently added items."""
    for i, item in enumerate(items, 1):
        title = item.get("title", "Unknown")
        item_type = item.get("type", "Unknown")
        year = item.get("year", "N/A")
        added = item.get("addedAt", "N/A")
        show = item.get("show", "")
        prefix = f"{show} - " if show else ""
        print(f"  [{i}] {prefix}{title} ({year}) - Type: {item_type} - Added: {added}")


if __name__ == "__main__":
    lib = sys.argv[1] if len(sys.argv) > 1 else None
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    results = get_recently_added(library_name=lib, limit=count)
    display_items(results)

    # Save results to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "plex_recently_added.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

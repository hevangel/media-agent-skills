"""
Search for media items on the Jellyfin server.
Supports searching by term, year, and media type.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def search_media(term, media_type=None, year=None, limit=20):
    """
    Search for media items by name, type, and/or year.

    Args:
        term (str): Search query string.
        media_type (str, optional): Filter by type (e.g. 'Movie', 'Series', 'Episode', 'Audio').
        year (int, optional): Filter by production year.
        limit (int): Maximum number of results.

    Returns:
        list: A list of matching item dicts.
    """
    client = get_jellyfin_client()

    print(f"Searching for '{term}' (type={media_type}, year={year}, limit={limit})...")
    result = client.jellyfin.search_media_items(
        term=term,
        media=media_type,
        year=year,
        limit=limit,
    )
    items = result.get("Items", [])
    total = result.get("TotalRecordCount", len(items))

    print(f"Found {total} total results, retrieved {len(items)}.")
    return items


def display_results(items):
    """Pretty print search results."""
    for i, item in enumerate(items, 1):
        name = item.get("Name", "Unknown")
        item_type = item.get("Type", "Unknown")
        year = item.get("ProductionYear", "N/A")
        item_id = item.get("Id", "N/A")
        print(f"  [{i}] {name} ({year}) - Type: {item_type} - ID: {item_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_media.py <search_term> [media_type] [year]")
        print("  media_type: Movie, Series, Episode, Audio, etc.")
        sys.exit(1)

    search_term = sys.argv[1]
    media = sys.argv[2] if len(sys.argv) > 2 else None
    yr = int(sys.argv[3]) if len(sys.argv) > 3 else None

    results = search_media(search_term, media_type=media, year=yr)
    display_results(results)

    # Save results to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "jellyfin_search_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

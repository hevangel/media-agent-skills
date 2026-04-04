"""
Get all items from a specific Jellyfin library.
Supports filtering by media type (Movie, Series, Episode, Audio, etc.).
"""

import json
import sys
from pathlib import Path

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def get_library_items(parent_id, media_type=None, limit=100):
    """
    Get items from a specific library folder.

    Args:
        parent_id (str): The library/parent folder ID.
        media_type (str, optional): Filter by item type (e.g. 'Movie', 'Series', 'Episode', 'Audio').
        limit (int): Maximum number of items to return.

    Returns:
        list: A list of item dicts.
    """
    client = get_jellyfin_client()

    params = {
        'ParentId': parent_id,
        'Recursive': True,
        'Limit': limit,
        'Fields': "Path,Genres,SortName,Studios,Overview,DateCreated,People,ProviderIds,Tags,MediaSources,PrimaryImageAspectRatio",
    }
    if media_type:
        params['IncludeItemTypes'] = media_type

    print(f"Fetching items from library {parent_id} (type={media_type}, limit={limit})...")
    result = client.jellyfin.user_items(params=params)
    items = result.get("Items", [])
    total = result.get("TotalRecordCount", len(items))

    print(f"Found {total} total items, retrieved {len(items)}.")
    return items


def display_items(items):
    """Pretty print item summaries."""
    for i, item in enumerate(items, 1):
        name = item.get("Name", "Unknown")
        item_type = item.get("Type", "Unknown")
        year = item.get("ProductionYear", "N/A")
        item_id = item.get("Id", "N/A")
        print(f"  [{i}] {name} ({year}) - Type: {item_type} - ID: {item_id}")


if __name__ == "__main__":
    # Usage: python get_library_items.py <library_id> [media_type]
    if len(sys.argv) < 2:
        print("Usage: python get_library_items.py <library_id> [media_type]")
        print("  media_type: Movie, Series, Episode, Audio, MusicAlbum, etc.")
        print("\nRun list_libraries.py first to find library IDs.")
        sys.exit(1)

    library_id = sys.argv[1]
    media = sys.argv[2] if len(sys.argv) > 2 else None
    items = get_library_items(library_id, media_type=media)
    display_items(items)

    # Save results to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "jellyfin_library_items.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

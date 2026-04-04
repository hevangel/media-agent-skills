"""
Get recently added items from the Jellyfin server.
Supports filtering by media type and library.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def get_recently_added(media_type=None, parent_id=None, limit=20):
    """
    Get recently added items.

    Args:
        media_type (str, optional): Filter by type (e.g. 'Movie', 'Series', 'Episode', 'Audio').
        parent_id (str, optional): Restrict to a specific library.
        limit (int): Maximum number of items to return.

    Returns:
        list: A list of recently added item dicts.
    """
    client = get_jellyfin_client()

    print(f"Fetching recently added items (type={media_type}, library={parent_id}, limit={limit})...")
    items = client.jellyfin.get_recently_added(
        media=media_type,
        parent_id=parent_id,
        limit=limit,
    )

    # get_recently_added returns a list directly (not paginated)
    if isinstance(items, dict):
        items = items.get("Items", [])

    print(f"Retrieved {len(items)} recently added items.")
    return items


def display_items(items):
    """Pretty print recently added items."""
    for i, item in enumerate(items, 1):
        name = item.get("Name", "Unknown")
        item_type = item.get("Type", "Unknown")
        year = item.get("ProductionYear", "N/A")
        date_created = item.get("DateCreated", "N/A")
        print(f"  [{i}] {name} ({year}) - Type: {item_type} - Added: {date_created}")


if __name__ == "__main__":
    media = sys.argv[1] if len(sys.argv) > 1 else None
    lib_id = sys.argv[2] if len(sys.argv) > 2 else None
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    results = get_recently_added(media_type=media, parent_id=lib_id, limit=count)
    display_items(results)

    # Save results to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "jellyfin_recently_added.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

"""
Get detailed metadata for a specific Jellyfin item.
Fetches full item info including genres, overview, people, provider IDs, etc.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def get_item_details(item_id):
    """
    Get full metadata for a single item.

    Args:
        item_id (str): The Jellyfin item UUID.

    Returns:
        dict: Full item metadata.
    """
    client = get_jellyfin_client()

    print(f"Fetching details for item {item_id}...")
    item = client.jellyfin.get_item(item_id)

    name = item.get("Name", "Unknown")
    item_type = item.get("Type", "Unknown")
    year = item.get("ProductionYear", "N/A")
    overview = item.get("Overview", "No overview available.")
    genres = item.get("Genres", [])
    studios = item.get("Studios", [])
    people = item.get("People", [])
    provider_ids = item.get("ProviderIds", {})
    path = item.get("Path", "N/A")
    date_created = item.get("DateCreated", "N/A")
    community_rating = item.get("CommunityRating", "N/A")
    official_rating = item.get("OfficialRating", "N/A")
    tags = item.get("Tags", [])

    print(f"\n{'='*80}")
    print(f"  Name: {name}")
    print(f"  Type: {item_type}")
    print(f"  Year: {year}")
    print(f"  Rating: {community_rating} (Official: {official_rating})")
    print(f"  Genres: {', '.join(genres) if genres else 'N/A'}")
    print(f"  Studios: {', '.join(s.get('Name', '') for s in studios) if studios else 'N/A'}")
    print(f"  Tags: {', '.join(tags) if tags else 'N/A'}")
    print(f"  Path: {path}")
    print(f"  Date Created: {date_created}")
    print(f"  Provider IDs: {provider_ids}")
    print(f"  Overview: {overview[:200]}{'...' if len(overview) > 200 else ''}")

    if people:
        print(f"  People:")
        for person in people[:10]:
            role = person.get("Role", "")
            role_str = f" as {role}" if role else ""
            print(f"    - {person.get('Name', 'Unknown')} ({person.get('Type', 'Unknown')}{role_str})")

    print(f"{'='*80}")
    return item


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_item_details.py <item_id>")
        print("\nRun search_media.py or get_library_items.py first to find item IDs.")
        sys.exit(1)

    target_id = sys.argv[1]
    details = get_item_details(target_id)

    # Save to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "jellyfin_item_details.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2, ensure_ascii=False)
    print(f"\nDetails saved to {output_path}")

"""
Export all items from a Jellyfin library with full metadata to a JSON file.
Fetches each item's details for a complete export.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def dump_library_to_json(parent_id, media_type=None, output_path=None):
    """
    Export all items from a library with full metadata.

    Args:
        parent_id (str): The library folder ID.
        media_type (str, optional): Filter by type (e.g. 'Movie', 'Series').
        output_path (str, optional): Path to write JSON output.

    Returns:
        list: A list of item dicts with full metadata.
    """
    client = get_jellyfin_client()

    params = {
        'ParentId': parent_id,
        'Recursive': True,
        'Fields': "Path,Genres,SortName,Studios,Overview,DateCreated,People,"
                  "ProviderIds,Tags,MediaSources,PrimaryImageAspectRatio,"
                  "CumulativeRunTimeTicks,OfficialRating",
        'Limit': 0,  # 0 = no limit, get all items
    }
    if media_type:
        params['IncludeItemTypes'] = media_type

    print(f"Fetching all items from library {parent_id}...")
    result = client.jellyfin.user_items(params=params)
    items = result.get("Items", [])
    total = result.get("TotalRecordCount", len(items))
    print(f"Found {total} items, processing...")

    # Build export list with key metadata
    export_data = []
    for i, item in enumerate(items):
        people = item.get("People", [])
        directors = [p.get("Name") for p in people if p.get("Type") == "Director"]
        actors = [
            {"name": p.get("Name"), "role": p.get("Role", "")}
            for p in people if p.get("Type") == "Actor"
        ]
        studios = [s.get("Name") for s in item.get("Studios", []) if s.get("Name")]
        runtime_ticks = item.get("CumulativeRunTimeTicks") or item.get("RunTimeTicks")
        runtime_minutes = round(runtime_ticks / 600_000_000, 1) if runtime_ticks else None

        entry = {
            "id": item.get("Id"),
            "name": item.get("Name"),
            "sort_name": item.get("SortName"),
            "type": item.get("Type"),
            "year": item.get("ProductionYear"),
            "overview": item.get("Overview", ""),
            "genres": item.get("Genres", []),
            "tags": item.get("Tags", []),
            "studios": studios,
            "directors": directors,
            "actors": actors[:5],  # Limit to top 5 actors
            "community_rating": item.get("CommunityRating"),
            "official_rating": item.get("OfficialRating"),
            "runtime_minutes": runtime_minutes,
            "provider_ids": item.get("ProviderIds", {}),
            "path": item.get("Path"),
            "date_created": item.get("DateCreated"),
        }
        export_data.append(entry)

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(items)} items...")

    print(f"Processed all {len(items)} items.")

    # Save to file
    if output_path is None:
        temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        output_path = str(temp_dir / "jellyfin_library_dump.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    print(f"\nExported {len(export_data)} items to {output_path}")

    return export_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dump_library_to_json.py <library_id> [media_type]")
        print("\nRun list_libraries.py first to find library IDs.")
        sys.exit(1)

    lib_id = sys.argv[1]
    media = sys.argv[2] if len(sys.argv) > 2 else None
    dump_library_to_json(lib_id, media_type=media)

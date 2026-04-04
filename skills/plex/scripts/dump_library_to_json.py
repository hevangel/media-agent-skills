"""
Export all items from a Plex library with full metadata to a JSON file.
Fetches each item's details for a complete export.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def dump_library_to_json(library_name, libtype=None, output_path=None):
    """
    Export all items from a library with full metadata.

    Args:
        library_name (str): The library section name.
        libtype (str, optional): Filter by type (e.g. 'movie', 'show').
        output_path (str, optional): Path to write JSON output.

    Returns:
        list: A list of item dicts with full metadata.
    """
    plex = get_plex_client()
    print(f"Fetching all items from library '{library_name}'...")

    section = plex.library.section(library_name)

    if libtype:
        items = section.search(libtype=libtype)
    else:
        items = section.all()

    print(f"Found {len(items)} items, processing...")

    export_data = []
    for i, item in enumerate(items):
        # Build a rich metadata dict
        entry = {
            "ratingKey": item.ratingKey,
            "title": item.title,
            "type": item.type,
            "year": getattr(item, "year", None),
            "summary": getattr(item, "summary", ""),
            "rating": getattr(item, "rating", None),
            "audienceRating": getattr(item, "audienceRating", None),
            "contentRating": getattr(item, "contentRating", None),
            "studio": getattr(item, "studio", None),
            "addedAt": str(getattr(item, "addedAt", "N/A")),
            "updatedAt": str(getattr(item, "updatedAt", "N/A")),
            "viewCount": getattr(item, "viewCount", 0),
        }

        # Genres
        if hasattr(item, "genres") and item.genres:
            entry["genres"] = [g.tag for g in item.genres]

        # Directors
        if hasattr(item, "directors") and item.directors:
            entry["directors"] = [d.tag for d in item.directors]

        # Actors (top 5)
        if hasattr(item, "roles") and item.roles:
            entry["actors"] = [
                {"name": r.tag, "role": getattr(r, "role", "")}
                for r in item.roles[:5]
            ]

        # Duration in minutes
        duration = getattr(item, "duration", None)
        if duration:
            entry["duration_minutes"] = round(duration / 60000, 1)

        # File paths
        if hasattr(item, "media") and item.media:
            files = []
            for m in item.media:
                if hasattr(m, "parts") and m.parts:
                    files.extend([p.file for p in m.parts if hasattr(p, "file")])
            if files:
                entry["files"] = files

        # GUIDs (IMDB, TMDB, TVDB)
        if hasattr(item, "guids") and item.guids:
            entry["guids"] = [g.id for g in item.guids]

        export_data.append(entry)

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(items)} items...")

    print(f"Processed all {len(items)} items.")

    # Save to file
    if output_path is None:
        temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        output_path = str(temp_dir / "plex_library_dump.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nExported {len(export_data)} items to {output_path}")

    return export_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dump_library_to_json.py <library_name> [libtype] [output_path]")
        print("  libtype: movie, show, artist, etc.")
        print("\nRun list_libraries.py first to find library names.")
        sys.exit(1)

    name = sys.argv[1]
    media = sys.argv[2] if len(sys.argv) > 2 else None
    out = sys.argv[3] if len(sys.argv) > 3 else None
    dump_library_to_json(name, libtype=media, output_path=out)

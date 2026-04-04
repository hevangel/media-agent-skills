"""
Get detailed metadata for a specific Plex item by rating key.
Fetches full item info including genres, summary, actors, directors, etc.
"""

import json
import sys
from pathlib import Path

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def get_item_details(rating_key):
    """
    Get full metadata for a single item.

    Args:
        rating_key (int|str): The Plex item rating key (ID).

    Returns:
        dict: Full item metadata.
    """
    plex = get_plex_client()
    print(f"Fetching details for item {rating_key}...")

    item = plex.fetchItem(int(rating_key))

    # Build details dict
    details = {
        "title": item.title,
        "type": item.type,
        "ratingKey": item.ratingKey,
        "year": getattr(item, "year", None),
        "summary": getattr(item, "summary", ""),
        "rating": getattr(item, "rating", None),
        "audienceRating": getattr(item, "audienceRating", None),
        "contentRating": getattr(item, "contentRating", None),
        "duration": getattr(item, "duration", None),
        "addedAt": str(getattr(item, "addedAt", "N/A")),
        "updatedAt": str(getattr(item, "updatedAt", "N/A")),
        "viewCount": getattr(item, "viewCount", 0),
    }

    # Genres
    if hasattr(item, "genres") and item.genres:
        details["genres"] = [g.tag for g in item.genres]

    # Directors (movies/episodes)
    if hasattr(item, "directors") and item.directors:
        details["directors"] = [d.tag for d in item.directors]

    # Actors/Roles
    if hasattr(item, "roles") and item.roles:
        details["actors"] = [
            {"name": r.tag, "role": getattr(r, "role", "")}
            for r in item.roles[:10]
        ]

    # Studios
    if hasattr(item, "studio"):
        details["studio"] = item.studio

    # Media info (resolution, codec, etc.)
    if hasattr(item, "media") and item.media:
        media_info = []
        for m in item.media:
            m_entry = {
                "videoResolution": getattr(m, "videoResolution", None),
                "videoCodec": getattr(m, "videoCodec", None),
                "audioCodec": getattr(m, "audioCodec", None),
                "container": getattr(m, "container", None),
                "bitrate": getattr(m, "bitrate", None),
            }
            # File paths
            if hasattr(m, "parts") and m.parts:
                m_entry["files"] = [p.file for p in m.parts if hasattr(p, "file")]
            media_info.append(m_entry)
        details["media"] = media_info

    # TV Show specifics
    if hasattr(item, "grandparentTitle") and item.grandparentTitle:
        details["show"] = item.grandparentTitle
    if hasattr(item, "parentTitle") and item.parentTitle:
        details["season"] = item.parentTitle
    if hasattr(item, "index"):
        details["episodeNumber"] = item.index
    if hasattr(item, "parentIndex"):
        details["seasonNumber"] = item.parentIndex

    # Provider IDs (IMDB, TMDB, TVDB)
    if hasattr(item, "guids") and item.guids:
        details["guids"] = [g.id for g in item.guids]

    # Display
    print(f"\n{'='*80}")
    print(f"  Title: {details['title']}")
    print(f"  Type: {details['type']}")
    print(f"  Year: {details.get('year', 'N/A')}")
    print(f"  Rating: {details.get('rating', 'N/A')} (Audience: {details.get('audienceRating', 'N/A')})")
    print(f"  Content Rating: {details.get('contentRating', 'N/A')}")
    print(f"  Genres: {', '.join(details.get('genres', [])) or 'N/A'}")
    print(f"  Studio: {details.get('studio', 'N/A')}")
    if details.get("directors"):
        print(f"  Directors: {', '.join(details['directors'])}")
    if details.get("actors"):
        for actor in details["actors"][:5]:
            role = f" as {actor['role']}" if actor.get("role") else ""
            print(f"    - {actor['name']}{role}")
    if details.get("guids"):
        print(f"  GUIDs: {details['guids']}")
    summary = details.get("summary", "")
    print(f"  Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}")
    print(f"{'='*80}")

    return details


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_item_details.py <rating_key>")
        print("\nRun search_media.py or get_library_items.py first to find rating keys.")
        sys.exit(1)

    target_key = sys.argv[1]
    details = get_item_details(target_key)

    # Save to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "plex_item_details.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nDetails saved to {output_path}")

"""
Dump Audiobookshelf Library Items to JSON
Exports all audiobooks from a specified library to a JSON file.
"""

import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration
SERVER_URL = os.getenv("AUDIOBOOKSHELF_HOST", "http://localhost/audiobookshelf")
API_KEY = os.getenv("AUDIOBOOKSHELF_API_KEY")

# Known library IDs (get these from list_libraries.py)
NON_FICTION_LIBRARY_ID = "acca13d4-b735-4abd-a9bd-8d7d429fa93f"
FICTION_LIBRARY_ID = "0adc6ee8-0ba4-4f53-a62d-91fda9be3b17"
LIGHT_NOVEL_LIBRARY_ID = "ee5cc086-c8dd-48f6-85d4-bdc07e0cb854"


def dump_library_to_json(library_id: str, output_filename: str):
    """
    Dump all items from a library to JSON file.
    
    Args:
        library_id: The library ID to dump
        output_filename: Name of the output JSON file
    """
    print(f"Fetching items from library {library_id}...")
    
    # Fetch library items using REST API
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SERVER_URL}/api/libraries/{library_id}/items"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    items = data.get("results", [])
    
    print(f"Found {len(items)} items")
    
    # Convert items to simplified format
    items_data = []
    for item in items:
        try:
            media = item.get("media", {})
            metadata = media.get("metadata", {})
            
            item_dict = {
                "id": item.get("id"),
                "media_type": item.get("mediaType"),
                "library_id": item.get("libraryId"),
                "folder_id": item.get("folderId"),
                "path": item.get("path"),
                "added_at": item.get("addedAt"),
                "updated_at": item.get("updatedAt"),
                "media": {
                    "duration": media.get("duration"),
                    "size": media.get("size"),
                    "num_tracks": len(media.get("tracks", [])),
                    "metadata": {
                        "title": metadata.get("title"),
                        "subtitle": metadata.get("subtitle"),
                        "authors": [author.get("name") for author in metadata.get("authors", [])],
                        "narrators": metadata.get("narrators", []),
                        "series": [{"name": s.get("name"), "sequence": s.get("sequence")}
                                 for s in metadata.get("series", [])],
                        "genres": metadata.get("genres", []),
                        "published_year": metadata.get("publishedYear"),
                        "published": metadata.get("published"),
                        "publisher": metadata.get("publisher"),
                        "description": metadata.get("description"),
                        "isbn": metadata.get("isbn"),
                        "asin": metadata.get("asin"),
                        "language": metadata.get("language"),
                        "explicit": metadata.get("explicit", False),
                    }
                }
            }
            
            items_data.append(item_dict)
        except Exception as e:
            print(f"Error processing item {item.get('id')}: {e}")
            continue
    
    # Sort by title
    items_data.sort(key=lambda x: x.get("media", {}).get("metadata", {}).get("title", "").lower())
    
    # Save to JSON file
    output_path = Path(output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSuccessfully dumped {len(items_data)} items to {output_path}")
    print(f"Total size: {output_path.stat().st_size / 1024:.2f} KB")
    
    # Print summary
    print(f"\nLibrary Summary:")
    print(f"  Total Items: {len(items_data)}")
    
    authors = set()
    for item in items_data:
        item_authors = item.get("media", {}).get("metadata", {}).get("authors", [])
        authors.update([a for a in item_authors if a])  # Filter out None/empty
    print(f"  Unique Authors: {len(authors)}")
    
    total_duration = sum(item.get("media", {}).get("duration", 0) for item in items_data)
    print(f"  Total Duration: {total_duration / 3600:.2f} hours")
    
    return items_data


if __name__ == "__main__":
    # Example: Dump Non-Fiction library
    dump_library_to_json(NON_FICTION_LIBRARY_ID, "nonfiction.json")
    
    # Example: Dump Fiction library
    # dump_library_to_json(FICTION_LIBRARY_ID, "fiction.json")
    
    # Example: Dump Light Novel library
    # dump_library_to_json(LIGHT_NOVEL_LIBRARY_ID, "light_novels.json")

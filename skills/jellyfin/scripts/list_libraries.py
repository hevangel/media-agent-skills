"""
List all media libraries on the Jellyfin server.
Demonstrates API key authentication and library listing.
"""

import json

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def list_libraries():
    """
    List all media libraries (virtual folders) on the Jellyfin server.

    Returns:
        list: A list of library dicts with Name, ItemId, CollectionType, etc.
    """
    client = get_jellyfin_client()
    print("Fetching media libraries...")

    libraries = client.jellyfin.virtual_folders()

    print(f"\nFound {len(libraries)} libraries:\n")
    print("-" * 80)

    for lib in libraries:
        name = lib.get("Name", "Unknown")
        item_id = lib.get("ItemId", "N/A")
        collection_type = lib.get("CollectionType", "N/A")
        locations = lib.get("Locations", [])
        print(f"  Name: {name}")
        print(f"  Item ID: {item_id}")
        print(f"  Collection Type: {collection_type}")
        print(f"  Locations: {locations}")
        print("-" * 80)

    return libraries


if __name__ == "__main__":
    result = list_libraries()
    print(f"\nTotal libraries: {len(result)}")

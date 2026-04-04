"""
List all media libraries on the Plex server.
Demonstrates token authentication and library listing.
"""

import json

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def list_libraries():
    """
    List all media libraries (sections) on the Plex server.

    Returns:
        list: A list of library dicts with title, type, key, totalSize, etc.
    """
    plex = get_plex_client()
    print("Fetching media libraries...")

    libraries = plex.library.sections()

    print(f"\nFound {len(libraries)} libraries:\n")
    print("-" * 80)

    results = []
    for lib in libraries:
        info = {
            "title": lib.title,
            "type": lib.type,
            "key": lib.key,
            "totalSize": lib.totalSize,
            "uuid": lib.uuid,
            "locations": lib.locations,
            "agent": lib.agent,
            "scanner": lib.scanner,
            "updatedAt": str(lib.updatedAt) if lib.updatedAt else "N/A",
        }
        results.append(info)

        print(f"  Title: {lib.title}")
        print(f"  Type: {lib.type}")
        print(f"  Key: {lib.key}")
        print(f"  Total Items: {lib.totalSize}")
        print(f"  Locations: {lib.locations}")
        print(f"  Updated At: {lib.updatedAt}")
        print("-" * 80)

    return results


if __name__ == "__main__":
    result = list_libraries()
    print(f"\nTotal libraries: {len(result)}")

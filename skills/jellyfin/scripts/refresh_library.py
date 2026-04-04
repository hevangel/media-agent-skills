"""
Trigger a library scan / refresh on the Jellyfin server.
Supports full library refresh or refreshing a specific item.
"""

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def refresh_all_libraries():
    """
    Trigger a full library scan on the Jellyfin server.
    """
    client = get_jellyfin_client()
    print("Triggering full library refresh...")
    client.jellyfin.refresh_library()
    print("Library refresh triggered successfully.")


def refresh_item(item_id, preset=None):
    """
    Refresh metadata for a specific item.

    Args:
        item_id (str): The item UUID to refresh.
        preset (str, optional): 'missing' to search for missing metadata,
                                'replace' to replace all metadata.
    """
    client = get_jellyfin_client()
    print(f"Refreshing item {item_id} (preset={preset})...")
    client.jellyfin.refresh_item(item_id, preset=preset)
    print(f"Item {item_id} refresh triggered successfully.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        target_id = sys.argv[1]
        p = sys.argv[2] if len(sys.argv) > 2 else "missing"
        refresh_item(target_id, preset=p)
    else:
        refresh_all_libraries()

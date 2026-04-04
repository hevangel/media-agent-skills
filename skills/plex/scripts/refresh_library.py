"""
Trigger a library scan / refresh on the Plex server.
Supports refreshing all libraries or a specific library by name.
"""

import sys

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def refresh_all_libraries():
    """
    Trigger a refresh on all Plex libraries.
    """
    plex = get_plex_client()
    print("Triggering refresh on all libraries...")
    for section in plex.library.sections():
        section.refresh()
        print(f"  Refresh triggered for '{section.title}'.")
    print("All library refreshes triggered successfully.")


def refresh_library(library_name):
    """
    Trigger a refresh on a specific library.

    Args:
        library_name (str): The library section name to refresh.
    """
    plex = get_plex_client()
    print(f"Triggering refresh on library '{library_name}'...")
    section = plex.library.section(library_name)
    section.refresh()
    print(f"Library '{library_name}' refresh triggered successfully.")


def scan_library(library_name, path=None):
    """
    Scan a specific library, optionally limited to a path.

    Args:
        library_name (str): The library section name to scan.
        path (str, optional): Specific path within the library to scan.
    """
    plex = get_plex_client()
    section = plex.library.section(library_name)
    if path:
        print(f"Scanning path '{path}' in library '{library_name}'...")
        section.update(path=path)
    else:
        print(f"Scanning library '{library_name}'...")
        section.update()
    print(f"Scan triggered for '{library_name}' successfully.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        lib = sys.argv[1]
        scan_path = sys.argv[2] if len(sys.argv) > 2 else None
        if scan_path:
            scan_library(lib, path=scan_path)
        else:
            refresh_library(lib)
    else:
        refresh_all_libraries()

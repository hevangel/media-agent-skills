"""
Scan a Kavita library to trigger a rescan.
Useful after updating epub metadata to refresh Kavita's index.
"""

import requests
from typing import Optional, List

try:
    from config import SERVER_URL, API_KEY, USERNAME, PASSWORD
except ImportError:
    from .config import SERVER_URL, API_KEY, USERNAME, PASSWORD


def login_and_get_token() -> Optional[str]:
    """
    Login to Kavita and get JWT token.
    
    Returns:
        JWT token string or None if login fails
    """
    url = f"{SERVER_URL}/api/account/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Login failed with status {response.status_code}")
            return None
        data = response.json()
        return data.get('token')
    except Exception as e:
        print(f"Login error: {e}")
        return None


def get_headers(token: str) -> dict:
    """Get headers with JWT token authentication."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def list_libraries(token: str) -> Optional[List[dict]]:
    """
    List all libraries in Kavita.
    
    Args:
        token: JWT authentication token
        
    Returns:
        List of library dictionaries or None if failed
    """
    url = f"{SERVER_URL}/api/Library/libraries"
    headers = get_headers(token)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to list libraries: {response.status_code}")
            return None
        return response.json()
    except Exception as e:
        print(f"Error listing libraries: {e}")
        return None


def scan_library(token: str, library_id: int, force: bool = False) -> bool:
    """
    Trigger a scan of a specific library.
    
    Args:
        token: JWT authentication token
        library_id: ID of the library to scan
        force: If True, forces full rescan including cover refresh
        
    Returns:
        True if scan was triggered successfully
    """
    url = f"{SERVER_URL}/api/Library/scan"
    headers = get_headers(token)
    params = {
        "libraryId": library_id,
        "force": str(force).lower()
    }
    
    try:
        response = requests.post(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return True
        else:
            print(f"Scan failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error triggering scan: {e}")
        return False


def scan_library_by_name(library_name: str, force: bool = False) -> bool:
    """
    Scan a library by its name.
    
    Args:
        library_name: Name of the library (partial match supported)
        force: If True, forces full rescan including cover refresh
        
    Returns:
        True if scan was triggered successfully
        
    Example:
        scan_library_by_name("Youth Novel", force=True)
    """
    print("Logging into Kavita...")
    token = login_and_get_token()
    if not token:
        print("Failed to authenticate")
        return False
    
    print("Fetching libraries...")
    libraries = list_libraries(token)
    if not libraries:
        print("Failed to get libraries")
        return False
    
    # Find matching library
    target_lib = None
    print("\nAvailable libraries:")
    for lib in libraries:
        name = lib.get('name', 'Unknown')
        lib_id = lib.get('id')
        print(f"  - {name} (ID: {lib_id})")
        if library_name.lower() in name.lower():
            target_lib = lib
    
    if not target_lib:
        print(f"\nError: Library matching '{library_name}' not found!")
        return False
    
    lib_id = target_lib.get('id')
    lib_name = target_lib.get('name')
    
    print(f"\nTriggering scan for '{lib_name}' (ID: {lib_id})...")
    
    if scan_library(token, lib_id, force=force):
        print(f"✓ Scan triggered successfully for '{lib_name}'!")
        if force:
            print("  Force mode enabled - covers will be refreshed")
        print("  The scan is running in the background.")
        return True
    else:
        print(f"✗ Failed to trigger scan for '{lib_name}'")
        return False


def scan_all_libraries(force: bool = False) -> bool:
    """
    Trigger a scan of all libraries.
    
    Args:
        force: If True, forces full rescan including cover refresh
        
    Returns:
        True if scan was triggered successfully
    """
    print("Logging into Kavita...")
    token = login_and_get_token()
    if not token:
        print("Failed to authenticate")
        return False
    
    url = f"{SERVER_URL}/api/Library/scan-all"
    headers = get_headers(token)
    params = {"force": str(force).lower()}
    
    try:
        response = requests.post(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            print("✓ Scan triggered for all libraries")
            return True
        else:
            print(f"Scan failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Example: Scan the Youth Novel library."""
    scan_library_by_name("Youth Novel", force=True)


if __name__ == "__main__":
    main()

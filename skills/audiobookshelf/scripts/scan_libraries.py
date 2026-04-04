"""
Trigger Library Scans in Audiobookshelf
Use this after making changes to audiobook files to refresh metadata.
"""

import asyncio
import aiohttp
import requests

# Configuration
SERVER_URL = os.getenv("AUDIOBOOKSHELF_HOST", "http://localhost/audiobookshelf")
API_KEY = os.getenv("AUDIOBOOKSHELF_API_KEY", "your_api_key_here")
USERNAME = os.getenv("AUDIOBOOKSHELF_USERNAME", "your_username")
PASSWORD = os.getenv("AUDIOBOOKSHELF_PASSWORD", "your_password")


# =============================================================================
# GET API TOKEN (Login-based authentication)
# =============================================================================
async def get_api_token() -> str:
    """Get API token by logging in with username/password."""
    async with aiohttp.ClientSession() as session:
        login_url = f"{SERVER_URL}/login"
        login_data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        try:
            async with session.post(login_url, json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('user', {}).get('token')
                else:
                    print(f"Login failed: {response.status}")
                    return None
        except Exception as e:
            print(f"Login error: {e}")
            return None


# =============================================================================
# ASYNC LIBRARY SCAN
# =============================================================================
async def get_all_libraries(session: aiohttp.ClientSession, token: str) -> list:
    """Get all libraries from Audiobookshelf."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{SERVER_URL}/api/libraries"
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('libraries', [])
            else:
                print(f"Failed to get libraries: {response.status}")
                return []
    except Exception as e:
        print(f"Error getting libraries: {e}")
        return []


async def trigger_library_scan_async(
    session: aiohttp.ClientSession,
    token: str,
    library_id: str,
    library_name: str = "Unknown"
) -> bool:
    """
    Trigger a library scan via async API call.
    
    Args:
        session: aiohttp session
        token: API token
        library_id: ID of the library to scan
        library_name: Name for logging purposes
        
    Returns:
        True if scan was triggered successfully
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{SERVER_URL}/api/libraries/{library_id}/scan"
    
    try:
        async with session.post(url, headers=headers) as response:
            if response.status in [200, 202]:
                print(f"✓ Scan triggered for: {library_name}")
                return True
            else:
                print(f"✗ Scan failed for {library_name}: {response.status}")
                return False
    except Exception as e:
        print(f"✗ Scan error for {library_name}: {e}")
        return False


async def scan_all_libraries():
    """Scan all libraries in Audiobookshelf."""
    print("Audiobookshelf Full Library Rescan")
    print("=" * 40)
    
    # Get API token
    print("Getting API token...")
    api_token = await get_api_token()
    if not api_token:
        print("❌ Failed to get API token")
        return
    
    print("✓ API token obtained\n")
    
    async with aiohttp.ClientSession() as session:
        # Get all libraries
        libraries = await get_all_libraries(session, api_token)
        
        if not libraries:
            print("❌ No libraries found")
            return
        
        print(f"Found {len(libraries)} libraries:")
        for lib in libraries:
            print(f"  • {lib.get('name')} ({lib.get('mediaType')})")
        
        # Trigger scan for all libraries
        print(f"\nTriggering scans...")
        success_count = 0
        
        for library in libraries:
            lib_id = library.get('id')
            lib_name = library.get('name', 'Unknown')
            
            success = await trigger_library_scan_async(
                session, api_token, lib_id, lib_name
            )
            if success:
                success_count += 1
            
            # Small delay between scans
            await asyncio.sleep(1)
        
        print(f"\n✅ Triggered scans for {success_count}/{len(libraries)} libraries")


async def scan_specific_library(library_id: str):
    """Scan a specific library by ID."""
    print(f"Scanning library: {library_id}")
    
    api_token = await get_api_token()
    if not api_token:
        print("❌ Failed to get API token")
        return
    
    async with aiohttp.ClientSession() as session:
        await trigger_library_scan_async(session, api_token, library_id)


# =============================================================================
# SYNC LIBRARY SCAN
# =============================================================================
def trigger_library_scan_sync(library_id: str) -> bool:
    """
    Trigger a library scan using sync API call.
    
    Args:
        library_id: ID of the library to scan
        
    Returns:
        True if scan was triggered successfully
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SERVER_URL}/api/libraries/{library_id}/scan"
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code in [200, 202]:
            print(f"✓ Library scan triggered")
            return True
        else:
            print(f"✗ Scan failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return False


def get_libraries_sync() -> list:
    """Get all libraries using sync API call."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SERVER_URL}/api/libraries"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get('libraries', [])
    except requests.exceptions.RequestException as e:
        print(f"Error getting libraries: {e}")
        return []


def scan_all_libraries_sync():
    """Scan all libraries using sync API calls."""
    print("Getting libraries...")
    libraries = get_libraries_sync()
    
    if not libraries:
        print("No libraries found")
        return
    
    print(f"Found {len(libraries)} libraries\n")
    
    for lib in libraries:
        lib_id = lib.get('id')
        lib_name = lib.get('name', 'Unknown')
        print(f"Scanning: {lib_name}...", end=" ")
        trigger_library_scan_sync(lib_id)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("=== Async Scan All Libraries ===")
    asyncio.run(scan_all_libraries())
    
    # Or scan a specific library:
    # asyncio.run(scan_specific_library("d852a24d-c105-4b71-a0ab-5bc5070e49d5"))
    
    # Or use sync version:
    # print("\n=== Sync Scan All Libraries ===")
    # scan_all_libraries_sync()

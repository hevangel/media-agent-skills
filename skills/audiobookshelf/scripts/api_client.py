"""
Audiobookshelf API Client Setup
Demonstrates both async (aioaudiobookshelf) and sync (requests) client setup patterns.
"""

import asyncio
import aiohttp
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION - Update these values for your setup
# =============================================================================
SERVER_URL = os.getenv("AUDIOBOOKSHELF_HOST", "http://localhost/audiobookshelf")
API_KEY = os.getenv("AUDIOBOOKSHELF_API_KEY", "your_api_key_here")  # Get from Audiobookshelf Settings > Users > API Key
USERNAME = os.getenv("AUDIOBOOKSHELF_USERNAME", "your_username")
PASSWORD = os.getenv("AUDIOBOOKSHELF_PASSWORD", "your_password")

# Known library IDs (get these from list_libraries.py)
PODCASTS_LIBRARY_ID = "468db721-12e6-4d2d-963a-135123adabca"
NON_FICTION_LIBRARY_ID = "acca13d4-b735-4abd-a9bd-8d7d429fa93f"
FICTION_LIBRARY_ID = "0adc6ee8-0ba4-4f53-a62d-91fda9be3b17"
LIGHT_NOVEL_LIBRARY_ID = "ee5cc086-c8dd-48f6-85d4-bdc07e0cb854"
UNSORT_LIBRARY_ID = "aae1dc15-57f0-40d2-bebe-4a0a1a25dde0"


# =============================================================================
# ASYNC CLIENT SETUP (aioaudiobookshelf package)
# =============================================================================
async def get_async_client():
    """
    Get an async Audiobookshelf client using aioaudiobookshelf package.
    
    Usage:
        async with aiohttp.ClientSession() as session:
            abs_client = await get_async_client_with_session(session)
            # Use abs_client...
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=SERVER_URL,
            token=API_KEY
        )
        abs_client = await get_admin_client_by_token(session_config=session_config)
        return abs_client


async def get_async_client_with_session(session: aiohttp.ClientSession):
    """
    Get an async client using an existing aiohttp session.
    
    Args:
        session: An existing aiohttp.ClientSession
        
    Returns:
        Audiobookshelf admin client
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    session_config = SessionConfiguration(
        session=session,
        url=SERVER_URL,
        token=API_KEY
    )
    return await get_admin_client_by_token(session_config=session_config)


# =============================================================================
# ASYNC CLIENT WITH LOGIN (no API key required)
# =============================================================================
async def get_api_token_by_login() -> str:
    """
    Get API token by logging in with username/password.
    
    Returns:
        API token string or None if login failed
    """
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
# SYNC CLIENT SETUP (requests library)
# =============================================================================
def get_sync_headers() -> dict:
    """
    Get headers for sync API requests.
    
    Returns:
        Dict with Authorization and Content-Type headers
    """
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


def make_sync_get_request(endpoint: str) -> dict:
    """
    Make a sync GET request to the Audiobookshelf API.
    
    Args:
        endpoint: API endpoint (e.g., "/api/libraries")
        
    Returns:
        JSON response as dict
    """
    headers = get_sync_headers()
    url = f"{SERVER_URL}{endpoint}"
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def make_sync_patch_request(endpoint: str, payload: dict) -> dict:
    """
    Make a sync PATCH request to the Audiobookshelf API.
    
    Args:
        endpoint: API endpoint (e.g., "/api/items/{id}")
        payload: JSON payload to send
        
    Returns:
        JSON response as dict
    """
    headers = get_sync_headers()
    url = f"{SERVER_URL}{endpoint}"
    
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def make_sync_post_request(endpoint: str, payload: dict = None) -> dict:
    """
    Make a sync POST request to the Audiobookshelf API.
    
    Args:
        endpoint: API endpoint
        payload: Optional JSON payload to send
        
    Returns:
        JSON response as dict
    """
    headers = get_sync_headers()
    url = f"{SERVER_URL}{endpoint}"
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
async def example_async_usage():
    """Example of async API usage."""
    async with aiohttp.ClientSession() as session:
        abs_client = await get_async_client_with_session(session)
        
        # Get all libraries
        libraries = await abs_client.get_all_libraries()
        for lib in libraries:
            print(f"Library: {lib.name} (ID: {lib.id_})")


def example_sync_usage():
    """Example of sync API usage."""
    # Get all libraries
    data = make_sync_get_request("/api/libraries")
    
    for lib in data.get('libraries', []):
        print(f"Library: {lib.get('name')} (ID: {lib.get('id')})")


if __name__ == "__main__":
    # Run async example
    print("=== Async Example ===")
    asyncio.run(example_async_usage())
    
    print("\n=== Sync Example ===")
    example_sync_usage()

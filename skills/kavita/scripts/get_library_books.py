"""
Get all books (series) from a specific library in Kavita
Demonstrates fetching all series from a library using the deprecated /api/series/all endpoint
with proper libraryId query parameter filtering.
"""

import requests
import json

try:
    from config import SERVER_URL, USERNAME, PASSWORD
except ImportError:
    from .config import SERVER_URL, USERNAME, PASSWORD


def login_and_get_token():
    """Login to Kavita and get JWT token"""
    url = f"{SERVER_URL}/api/account/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        print(f"Attempting login to {url}...")
        response = requests.post(url, json=payload, timeout=10)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        response.raise_for_status()
        data = response.json()
        print("Login successful!")
        return data.get('token')
    except Exception as e:
        print(f"Login error: {e}")
        if hasattr(e, 'response'):
            print(f"Response text: {e.response.text}")
        return None


def get_headers(token):
    """Get headers with JWT token authentication"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def get_all_series(token, library_id):
    """
    Get all series (books) from a specific library
    
    IMPORTANT: libraryId must be a query parameter, NOT in the request body.
    The /api/series/all endpoint is deprecated but still functional.
    """
    headers = get_headers(token)
    url = f"{SERVER_URL}/api/series/all"
    
    # libraryId must be a query parameter to filter by library
    params = {
        "libraryId": library_id,
        "PageNumber": 0,
        "PageSize": 0  # 0 means "get all"
    }
    
    # Empty filter in the request body
    payload = {}
    
    try:
        print(f"\nFetching series from library {library_id}...")
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"API returned status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
        
        if not response.text or response.text.strip().startswith('<!doctype'):
            print("Got HTML response instead of JSON")
            return None
        
        data = response.json()
        print(f"✓ Found {len(data)} series")
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    # Example: Get all books from Calibre Library (ID: 1)
    LIBRARY_ID = 1  # Change this to your library ID
    
    # Login
    token = login_and_get_token()
    if not token:
        print("Failed to authenticate")
        return
    
    # Get all series from the library
    series_list = get_all_series(token, LIBRARY_ID)
    
    if not series_list:
        print("Could not fetch series data")
        return
    
    print(f"\nBooks in library {LIBRARY_ID}:")
    print("-" * 80)
    
    # Display first 10 books as example
    for i, series in enumerate(series_list[:10], 1):
        print(f"\n{i}. {series.get('name', 'Unknown')}")
        print(f"   ID: {series.get('id')}")
        print(f"   Pages: {series.get('pages', 0)}")
        print(f"   Format: {series.get('format')}")
        print(f"   Word Count: {series.get('wordCount', 0):,}")
    
    if len(series_list) > 10:
        print(f"\n... and {len(series_list) - 10} more books")
    
    # Optionally save to JSON
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(os.path.dirname(script_dir))
    temp_dir = os.path.join(workspace_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    output_file = os.path.join(temp_dir, "library_books.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(series_list, f, indent=2, ensure_ascii=False)
    print(f"\nFull data saved to: {output_file}")


if __name__ == "__main__":
    main()

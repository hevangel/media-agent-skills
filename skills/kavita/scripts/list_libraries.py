"""
List all libraries in Kavita
Demonstrates JWT authentication and library listing via the Kavita API.
"""

import requests
import json

try:
    from config import SERVER_URL, API_KEY, USERNAME, PASSWORD
except ImportError:
    from .config import SERVER_URL, API_KEY, USERNAME, PASSWORD


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


def list_libraries():
    """List all libraries in Kavita"""
    # First login to get token
    token = login_and_get_token()
    if not token:
        print("Failed to get authentication token")
        return None
    
    # The correct endpoint for listing libraries
    url = f"{SERVER_URL}/api/Library/libraries"
    headers = get_headers(token)
    
    try:
        print(f"\nFetching libraries from {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Request failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
        
        response.raise_for_status()
        
        # Check if response has content
        if not response.text:
            print("Empty response")
            return None
            
        libraries = response.json()
        
        if not libraries:
            print("No libraries found.")
            return None
        
        print(f"\n✓ Success! Found {len(libraries)} libraries\n")
        print(f"Found {len(libraries)} libraries in Kavita:\n")
        print("-" * 80)
        
        for lib in libraries:
            print(f"\nLibrary: {lib.get('name', 'Unknown')}")
            print(f"  ID: {lib.get('id')}")
            print(f"  Type: {lib.get('type', 'Unknown')}")
            
            # Show folders if available
            if 'folders' in lib and isinstance(lib['folders'], list):
                print(f"  Folders:")
                for folder in lib['folders']:
                    if isinstance(folder, dict):
                        print(f"    - {folder.get('path', 'Unknown path')}")
                    else:
                        print(f"    - {folder}")
        
        print("\n" + "-" * 80)
        
        # Save to JSON file
        output_file = "temp/kavita_libraries.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(libraries, f, indent=2, ensure_ascii=False)
        print(f"\nFull library data saved to: {output_file}")
        
        return libraries
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        if 'response' in locals():
            print(f"Response text: {response.text[:200]}")
        return None


if __name__ == "__main__":
    list_libraries()

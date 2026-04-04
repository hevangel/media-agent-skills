"""
Get detailed metadata for a series in Kavita
Demonstrates fetching series metadata including authors, year, summary, genres, and tags
using the /api/Series/metadata endpoint.
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
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Login failed with status {response.status_code}")
            return None
        
        data = response.json()
        print("Login successful!")
        return data.get('token')
    except Exception as e:
        print(f"Login error: {e}")
        return None


def get_headers(token):
    """Get headers with JWT token authentication"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def get_series_metadata(token, series_id):
    """
    Get detailed metadata for a series
    
    Returns SeriesMetadataDto containing:
    - summary: Book description
    - writers: List of authors (PersonDto[])
    - genres: List of genre tags
    - tags: List of tags
    - publishers: List of publishers
    - releaseYear: Publication year
    - language: BCP-47 language code
    - ageRating: Content rating
    - publicationStatus: Publication status
    - and more...
    """
    url = f"{SERVER_URL}/api/Series/metadata"
    headers = get_headers(token)
    params = {"seriesId": series_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get metadata: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def display_metadata(metadata):
    """Display metadata in a readable format"""
    if not metadata:
        print("No metadata available")
        return
    
    print("\nMetadata:")
    print("=" * 80)
    
    # Summary
    summary = metadata.get('summary')
    if summary:
        print(f"\nSummary:\n{summary[:200]}{'...' if len(summary) > 200 else ''}")
    
    # Authors (Writers)
    writers = metadata.get('writers', [])
    if writers:
        authors = [w.get('name') for w in writers if w.get('name')]
        print(f"\nAuthor(s): {', '.join(authors)}")
    
    # Publication info
    release_year = metadata.get('releaseYear')
    if release_year:
        print(f"Release Year: {release_year}")
    
    language = metadata.get('language')
    if language:
        print(f"Language: {language}")
    
    # Publishers
    publishers = metadata.get('publishers', [])
    if publishers:
        pub_names = [p.get('name') for p in publishers if p.get('name')]
        print(f"Publisher(s): {', '.join(pub_names)}")
    
    # Genres
    genres = metadata.get('genres', [])
    if genres:
        genre_names = [g.get('title') for g in genres if g.get('title')]
        print(f"Genres: {', '.join(genre_names)}")
    
    # Tags
    tags = metadata.get('tags', [])
    if tags:
        tag_names = [t.get('title') for t in tags if t.get('title')]
        print(f"Tags: {', '.join(tag_names)}")
    
    # Other metadata
    age_rating = metadata.get('ageRating')
    if age_rating is not None:
        print(f"Age Rating: {age_rating}")
    
    pub_status = metadata.get('publicationStatus')
    if pub_status is not None:
        status_map = {0: "Ongoing", 1: "Hiatus", 2: "Completed", 3: "Cancelled", 4: "Ended"}
        print(f"Publication Status: {status_map.get(pub_status, pub_status)}")


def main():
    # Example: Get metadata for a specific series
    SERIES_ID = 1  # Change this to your series ID
    
    # Login
    token = login_and_get_token()
    if not token:
        print("Failed to authenticate")
        return
    
    # Get series metadata
    print(f"\nFetching metadata for series ID {SERIES_ID}...")
    metadata = get_series_metadata(token, SERIES_ID)
    
    if metadata:
        display_metadata(metadata)
        
        # Save to JSON
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.dirname(os.path.dirname(script_dir))
        temp_dir = os.path.join(workspace_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        output_file = os.path.join(temp_dir, "series_metadata.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"\nFull metadata saved to: {output_file}")
    else:
        print("Could not fetch metadata")


if __name__ == "__main__":
    main()

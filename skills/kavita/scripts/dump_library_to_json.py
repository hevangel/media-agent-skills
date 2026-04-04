"""
Dump all books from a Kavita library to JSON with complete metadata
Combines series data with metadata (authors, year, summary, genres, tags)
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


def get_all_series(token, library_id):
    """Get all series from a library"""
    headers = get_headers(token)
    url = f"{SERVER_URL}/api/series/all"
    
    params = {
        "libraryId": library_id,
        "PageNumber": 0,
        "PageSize": 0
    }
    payload = {}
    
    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching series: {e}")
    
    return None


def get_series_metadata(token, series_id):
    """Get metadata for a series"""
    url = f"{SERVER_URL}/api/Series/metadata"
    headers = get_headers(token)
    params = {"seriesId": series_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        pass
    
    return None


def dump_library_books(token, library_id):
    """Dump all books from a library with full metadata"""
    print(f"\nFetching books from library ID {library_id}...")
    
    # Get all series
    series_list = get_all_series(token, library_id)
    if not series_list:
        print("Could not fetch books")
        return None
    
    print(f"Found {len(series_list)} books. Fetching metadata...\n")
    
    books = []
    books_with_metadata = 0
    
    for i, series in enumerate(series_list, 1):
        title = series.get('name', 'Unknown')
        print(f"Processing {i}/{len(series_list)}: {title[:80]}")
        
        series_id = series.get('id')
        series_metadata = None
        
        if series_id:
            series_metadata = get_series_metadata(token, series_id)
            if series_metadata:
                print(f"  ✓ Got metadata")
                books_with_metadata += 1
        
        # Build book info from SeriesDto
        book_info = {
            "id": series.get('id'),
            "title": series.get('name', 'Unknown'),
            "localizedName": series.get('localizedName'),
            "originalName": series.get('originalName'),
            "sortName": series.get('sortName'),
            "summary": None,
            "year": None,
            "releaseYear": None,
            "authors": [],
            "genres": [],
            "tags": [],
            "publishers": [],
            "language": None,
            "pages": series.get('pages', 0),
            "wordCount": series.get('wordCount', 0),
            "created": series.get('created'),
            "lastModified": series.get('lastChapterAdded'),
            "rating": series.get('userRating'),
            "format": series.get('format'),
            "libraryId": series.get('libraryId'),
            "libraryName": series.get('libraryName'),
        }
        
        # Merge metadata
        if series_metadata:
            book_info['summary'] = series_metadata.get('summary')
            book_info['releaseYear'] = series_metadata.get('releaseYear')
            book_info['year'] = series_metadata.get('releaseYear')
            book_info['language'] = series_metadata.get('language')
            book_info['ageRating'] = series_metadata.get('ageRating')
            book_info['publicationStatus'] = series_metadata.get('publicationStatus')
            
            # Extract writers (authors)
            writers = series_metadata.get('writers', [])
            if writers:
                book_info['authors'] = [w.get('name') for w in writers if w.get('name')]
            
            # Extract genres
            genres = series_metadata.get('genres', [])
            if genres:
                book_info['genres'] = [g.get('title') for g in genres if g.get('title')]
            
            # Extract tags
            tags = series_metadata.get('tags', [])
            if tags:
                book_info['tags'] = [t.get('title') for t in tags if t.get('title')]
            
            # Extract publishers
            publishers = series_metadata.get('publishers', [])
            if publishers:
                book_info['publishers'] = [p.get('name') for p in publishers if p.get('name')]
        
        books.append(book_info)
    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Total books: {len(books)}")
    print(f"  Books with metadata: {books_with_metadata}")
    print(f"  Books with authors: {sum(1 for b in books if b.get('authors'))}")
    print(f"  Books with year: {sum(1 for b in books if b.get('year'))}")
    print(f"  Books with summary: {sum(1 for b in books if b.get('summary'))}")
    print(f"{'='*80}")
    
    return books


def main():
    # Configuration
    import os
    LIBRARY_ID = 1  # Calibre Library - change this to your library ID
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(os.path.dirname(script_dir))
    temp_dir = os.path.join(workspace_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    OUTPUT_FILE = os.path.join(temp_dir, "library_books_dump.json")
    
    # Login
    token = login_and_get_token()
    if not token:
        print("Failed to authenticate")
        return
    
    # Dump books
    books = dump_library_books(token, LIBRARY_ID)
    
    if books:
        # Save to JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successfully dumped {len(books)} books to {OUTPUT_FILE}")
        
        # Show sample
        print(f"\nSample (first 3 books):")
        for book in books[:3]:
            print(f"\n  Title: {book['title']}")
            if book.get('authors'):
                print(f"  Author(s): {', '.join(book['authors'])}")
            if book.get('year'):
                print(f"  Year: {book['year']}")
            if book.get('genres'):
                print(f"  Genres: {', '.join(book['genres'])}")


if __name__ == "__main__":
    main()

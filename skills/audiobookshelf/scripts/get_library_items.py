"""
Get Library Items from Audiobookshelf
Fetch books from libraries with filtering and metadata extraction.
"""

import asyncio
import aiohttp
import requests
import re

# Configuration
SERVER_URL = "http://localhost/audiobookshelf"
API_KEY = "your_api_key_here"


# =============================================================================
# ASYNC METHODS (aioaudiobookshelf)
# =============================================================================
async def get_library_items_async(library_id: str) -> list:
    """
    Get all items from a library using aioaudiobookshelf.
    
    Args:
        library_id: The library ID to fetch items from
        
    Returns:
        List of library items
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=SERVER_URL,
            token=API_KEY
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        items = await abs_client.get_library_items(library_id=library_id)
        
        return items


async def get_book_details_async(book_id: str):
    """
    Get detailed information about a specific book.
    
    Args:
        book_id: The library item ID
        
    Returns:
        Book item with full details
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=SERVER_URL,
            token=API_KEY
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        item = await abs_client.get_library_item_book(book_id=book_id, expanded=True)
        
        return item


async def list_books_with_metadata(library_id: str):
    """
    List all books in a library with their metadata.
    
    Args:
        library_id: The library ID
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=SERVER_URL,
            token=API_KEY
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        
        # Get library info
        libraries = await abs_client.get_all_libraries()
        library_name = "Unknown"
        for lib in libraries:
            if lib.id_ == library_id:
                library_name = lib.name
                break
        
        print(f"Books in '{library_name}' library:")
        print("=" * 70)
        
        items = await abs_client.get_library_items(library_id=library_id)
        
        for i, item in enumerate(items, 1):
            media = item.media
            metadata = media.metadata
            
            title = metadata.title
            authors = []
            if hasattr(metadata, 'authors') and metadata.authors:
                authors = [a.name for a in metadata.authors]
            
            series_info = []
            if hasattr(metadata, 'series') and metadata.series:
                for s in metadata.series:
                    series_info.append(f"{s.name} #{s.sequence}")
            
            duration_hours = media.duration / 3600 if hasattr(media, 'duration') and media.duration else 0
            
            print(f"{i}. {title}")
            print(f"   Author(s): {', '.join(authors) if authors else 'Unknown'}")
            if series_info:
                print(f"   Series: {', '.join(series_info)}")
            print(f"   Duration: {duration_hours:.1f} hours")
            print(f"   Item ID: {item.id_}")
            print()


# =============================================================================
# SYNC METHODS (requests)
# =============================================================================
def get_library_items_sync(library_id: str) -> list:
    """
    Get all items from a library using sync API call.
    
    Args:
        library_id: The library ID
        
    Returns:
        List of items (dict format)
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SERVER_URL}/api/libraries/{library_id}/items"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching library items: {e}")
        return []


def list_books_sync(library_id: str):
    """
    List all books in a library with basic info.
    
    Args:
        library_id: The library ID
    """
    books = get_library_items_sync(library_id)
    
    print(f"Found {len(books)} books:")
    print("=" * 60)
    
    for i, book in enumerate(books, 1):
        media = book.get("media", {})
        metadata = media.get("metadata", {})
        
        title = metadata.get("title", "Unknown")
        authors = metadata.get("authors", [])
        author_names = [a.get("name", "") for a in authors]
        
        series = metadata.get("series", [])
        series_info = [f"{s.get('name')} #{s.get('sequence')}" for s in series]
        
        duration = media.get("duration", 0)
        duration_hours = duration / 3600 if duration else 0
        
        print(f"{i}. {title}")
        print(f"   Author(s): {', '.join(author_names) if author_names else 'Unknown'}")
        if series_info:
            print(f"   Series: {', '.join(series_info)}")
        print(f"   Duration: {duration_hours:.1f} hours")
        print(f"   Item ID: {book.get('id')}")
        print()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def extract_volume_number(title: str) -> int:
    """
    Extract volume number from a book title.
    
    Args:
        title: Book title (e.g., "86—EIGHTY-SIX Vol. 3")
        
    Returns:
        Volume number as int, or None if not found
    """
    match = re.search(r'Vol\.?\s*(\d+)', title)
    if match:
        return int(match.group(1))
    return None


def filter_books_by_author(books: list, author_name: str) -> list:
    """
    Filter books by author name (partial match).
    
    Args:
        books: List of book dicts
        author_name: Author name to search for
        
    Returns:
        Filtered list of books
    """
    filtered = []
    author_lower = author_name.lower()
    
    for book in books:
        media = book.get("media", {})
        metadata = media.get("metadata", {})
        authors = metadata.get("authors", [])
        
        for author in authors:
            if author_lower in author.get("name", "").lower():
                filtered.append(book)
                break
    
    return filtered


def filter_books_by_series(books: list, series_name: str) -> list:
    """
    Filter books by series name (partial match).
    
    Args:
        books: List of book dicts
        series_name: Series name to search for
        
    Returns:
        Filtered list of books
    """
    filtered = []
    series_lower = series_name.lower()
    
    for book in books:
        media = book.get("media", {})
        metadata = media.get("metadata", {})
        series_list = metadata.get("series", [])
        
        for series in series_list:
            if series_lower in series.get("name", "").lower():
                filtered.append(book)
                break
    
    return filtered


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    # Example library IDs
    AUDIOBOOKS_LIBRARY_ID = "d852a24d-c105-4b71-a0ab-5bc5070e49d5"
    LIGHT_NOVELS_LIBRARY_ID = "dd2194dd-b243-4808-a0fd-8379369c9bf4"
    
    print("=== Sync: List Books ===\n")
    list_books_sync(LIGHT_NOVELS_LIBRARY_ID)
    
    print("\n=== Async: List Books with Metadata ===\n")
    asyncio.run(list_books_with_metadata(LIGHT_NOVELS_LIBRARY_ID))
    
    # Example: Filter by author
    print("\n=== Filter by Author ===")
    books = get_library_items_sync(AUDIOBOOKS_LIBRARY_ID)
    asimov_books = filter_books_by_author(books, "Asimov")
    print(f"Found {len(asimov_books)} books by Asimov")

"""
Update Book Metadata in Audiobookshelf
Demonstrates how to update book metadata including series information.
"""

import asyncio
import aiohttp
import requests

# Configuration
SERVER_URL = "http://localhost/audiobookshelf"
API_KEY = "your_api_key_here"


# =============================================================================
# ASYNC UPDATE (Direct API call with aiohttp)
# =============================================================================
async def update_book_series_async(book_id: str, series_name: str, sequence: str):
    """
    Update series information for a book using async API call.
    
    Args:
        book_id: The library item ID of the book
        series_name: Name of the series
        sequence: Book number in the series (as string)
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        url = f"{SERVER_URL}/api/items/{book_id}/media"
        
        payload = {
            'metadata': {
                'series': [
                    {
                        'name': series_name,
                        'sequence': sequence
                    }
                ]
            }
        }
        
        async with session.patch(url, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✓ Successfully updated series: {series_name} (Book {sequence})")
                return result
            else:
                error_text = await response.text()
                print(f"✗ Failed with status {response.status}: {error_text}")
                return None


async def update_book_metadata_async(
    book_id: str,
    title: str = None,
    subtitle: str = None,
    author: str = None,
    narrator: str = None,
    series: list = None,
    genres: list = None,
    description: str = None
):
    """
    Update multiple metadata fields for a book.
    
    Args:
        book_id: The library item ID
        title: Book title
        subtitle: Book subtitle
        author: Author name (will be converted to author list format)
        narrator: Narrator name
        series: List of series dicts [{'name': 'Series Name', 'sequence': '1'}]
        genres: List of genre strings
        description: Book description
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        url = f"{SERVER_URL}/api/items/{book_id}/media"
        
        # Build metadata payload with only provided fields
        metadata = {}
        
        if title:
            metadata['title'] = title
        if subtitle:
            metadata['subtitle'] = subtitle
        if author:
            metadata['authors'] = [{'name': author}]
        if narrator:
            metadata['narrators'] = [{'name': narrator}]
        if series:
            metadata['series'] = series
        if genres:
            metadata['genres'] = genres
        if description:
            metadata['description'] = description
        
        payload = {'metadata': metadata}
        
        async with session.patch(url, headers=headers, json=payload) as response:
            if response.status == 200:
                print(f"✓ Successfully updated book: {book_id}")
                return await response.json()
            else:
                error_text = await response.text()
                print(f"✗ Failed: {error_text}")
                return None


# =============================================================================
# SYNC UPDATE (Using requests library)
# =============================================================================
def update_book_series_sync(book_id: str, series_name: str, sequence: str):
    """
    Update series information for a book using sync API call.
    
    Args:
        book_id: The library item ID of the book
        series_name: Name of the series
        sequence: Book number in the series (as string)
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SERVER_URL}/api/items/{book_id}/media"
    
    payload = {
        "metadata": {
            "series": [
                {
                    "name": series_name,
                    "sequence": str(sequence)
                }
            ]
        }
    }
    
    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✓ Updated: {series_name} (Book {sequence})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return False


def update_book_metadata_sync(book_id: str, metadata: dict):
    """
    Update book metadata using sync API call.
    
    Args:
        book_id: The library item ID
        metadata: Dict with metadata fields to update
        
    Example metadata:
        {
            'title': 'Book Title',
            'series': [{'name': 'Series', 'sequence': '1'}],
            'authors': [{'name': 'Author Name'}]
        }
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SERVER_URL}/api/items/{book_id}/media"
    payload = {"metadata": metadata}
    
    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error updating book {book_id}: {e}")
        return None


# =============================================================================
# BATCH UPDATE EXAMPLE
# =============================================================================
async def batch_update_series(books: list, series_name: str):
    """
    Update series information for multiple books.
    
    Args:
        books: List of dicts with 'id' and 'sequence' keys
        series_name: Name of the series
        
    Example books:
        [
            {'id': 'book-id-1', 'sequence': '1'},
            {'id': 'book-id-2', 'sequence': '2'},
        ]
    """
    print(f"Updating {len(books)} books in series: {series_name}")
    print("=" * 60)
    
    for book in books:
        await update_book_series_async(
            book_id=book['id'],
            series_name=series_name,
            sequence=book['sequence']
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    # Example: Update a single book's series
    book_id = "adec6290-68f9-4b49-9043-530e7271d6a0"
    
    print("=== Sync Update Example ===")
    update_book_series_sync(book_id, "Foundation", "1")
    
    print("\n=== Async Update Example ===")
    asyncio.run(update_book_series_async(book_id, "Foundation", "1"))
    
    print("\n=== Batch Update Example ===")
    foundation_books = [
        {'id': 'adec6290-68f9-4b49-9043-530e7271d6a0', 'sequence': '1'},
        {'id': 'd4bc97f4-1c62-4175-8d15-8a99b713d13e', 'sequence': '3'},
    ]
    asyncio.run(batch_update_series(foundation_books, "Foundation"))

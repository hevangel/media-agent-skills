"""
Author Search and Management in Audiobookshelf
Search, filter, and update author information.
"""

import asyncio
import aiohttp
import json

# Configuration
SERVER_URL = "http://localhost/audiobookshelf"
API_KEY = "your_api_key_here"


# =============================================================================
# GET AUTHORS
# =============================================================================
async def get_all_authors(library_id: str) -> list:
    """
    Get all authors from a library.
    
    Args:
        library_id: The library ID
        
    Returns:
        List of author objects
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=SERVER_URL,
            token=API_KEY
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        authors = await abs_client.get_library_authors(library_id=library_id)
        
        return authors


async def search_author(library_id: str, search_name: str):
    """
    Search for an author by name (partial match).
    
    Args:
        library_id: The library ID
        search_name: Author name to search for
        
    Returns:
        Matching author or None
    """
    authors = await get_all_authors(library_id)
    search_lower = search_name.lower()
    
    for author in authors:
        if search_lower in author.name.lower():
            return author
    
    return None


async def get_author_with_books(library_id: str, author_name: str):
    """
    Get author details including their books.
    
    Args:
        library_id: The library ID
        author_name: Author name to search for
        
    Returns:
        Tuple of (author, books_list) or (None, [])
    """
    from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=SERVER_URL,
            token=API_KEY
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        
        # Find the author
        library_authors = await abs_client.get_library_authors(library_id=library_id)
        
        author = None
        for a in library_authors:
            if author_name.lower() in a.name.lower():
                author = a
                break
        
        if not author:
            return None, []
        
        # Get author details with books
        author_details = await abs_client.get_author(
            author_id=author.id_,
            include_items=True
        )
        
        books = []
        if hasattr(author_details, 'library_items') and author_details.library_items:
            for item in author_details.library_items:
                media = item.media
                metadata = media.metadata
                
                book_info = {
                    'item_id': item.id_,
                    'title': metadata.title,
                    'subtitle': getattr(metadata, 'subtitle', None),
                    'series': [],
                    'published_year': getattr(metadata, 'published_year', None),
                    'duration': media.duration if hasattr(media, 'duration') else None
                }
                
                if hasattr(metadata, 'series') and metadata.series:
                    for series in metadata.series:
                        book_info['series'].append({
                            'id': series.id_,
                            'name': series.name,
                            'sequence': series.sequence
                        })
                
                books.append(book_info)
        
        return author_details, books


# =============================================================================
# AUTHORS WITHOUT PICTURES
# =============================================================================
async def get_authors_without_pictures(library_id: str) -> list:
    """
    Get all authors that don't have a profile picture.
    
    Args:
        library_id: The library ID
        
    Returns:
        List of author dicts without pictures
    """
    authors = await get_all_authors(library_id)
    
    authors_without_pictures = []
    
    for author in authors:
        has_picture = False
        
        if hasattr(author, 'image_path') and author.image_path:
            has_picture = True
        elif hasattr(author, 'imagePath') and author.imagePath:
            has_picture = True
        
        if not has_picture:
            author_data = {
                "id": author.id_,
                "name": author.name,
                "num_books": author.num_books if hasattr(author, 'num_books') else 0
            }
            authors_without_pictures.append(author_data)
    
    return authors_without_pictures


async def export_authors_without_pictures(library_id: str, output_file: str = "authors.json"):
    """
    Export authors without pictures to a JSON file.
    
    Args:
        library_id: The library ID
        output_file: Output JSON filename
    """
    authors = await get_authors_without_pictures(library_id)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(authors, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(authors)} authors without pictures to {output_file}")
    return authors


# =============================================================================
# UPDATE AUTHOR PHOTO
# =============================================================================
async def update_author_photo(author_id: str, image_url: str, author_name: str = None):
    """
    Update an author's profile photo.
    
    Args:
        author_id: The author ID
        image_url: URL to the author's image
        author_name: Author name (required by API)
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        url = f"{SERVER_URL}/api/authors/{author_id}"
        
        payload = {
            'name': author_name,
            'image': image_url
        }
        
        async with session.patch(url, headers=headers, json=payload) as response:
            if response.status in [200, 204]:
                print(f"✓ Updated photo for: {author_name}")
                return True
            else:
                error_text = await response.text()
                print(f"✗ Failed for {author_name}: {error_text}")
                return False


async def batch_update_author_photos(library_id: str, authors_file: str):
    """
    Update author photos from a JSON file.
    
    Args:
        library_id: The library ID
        authors_file: JSON file with author data (must have 'name' and 'image_url' fields)
        
    JSON format:
    [
        {"name": "Isaac Asimov", "image_url": "https://example.com/asimov.jpg"},
        ...
    ]
    """
    # Load authors from JSON
    with open(authors_file, 'r') as f:
        authors_data = json.load(f)
    
    print(f"Loaded {len(authors_data)} authors from {authors_file}")
    
    # Get library authors for ID lookup
    library_authors = await get_all_authors(library_id)
    
    updated_count = 0
    skipped_count = 0
    
    for author_info in authors_data:
        author_name = author_info.get('name')
        image_url = author_info.get('image_url')
        
        if not image_url:
            print(f"[SKIP] {author_name}: No image URL")
            skipped_count += 1
            continue
        
        # Find matching author
        matching_author = None
        for lib_author in library_authors:
            if lib_author.name.lower() == author_name.lower():
                matching_author = lib_author
                break
        
        if not matching_author:
            print(f"[SKIP] {author_name}: Not found in library")
            skipped_count += 1
            continue
        
        success = await update_author_photo(
            author_id=matching_author.id_,
            image_url=image_url,
            author_name=author_name
        )
        
        if success:
            updated_count += 1
    
    print(f"\n=== Update Summary ===")
    print(f"Updated: {updated_count}")
    print(f"Skipped: {skipped_count}")


# =============================================================================
# LIST AUTHORS
# =============================================================================
async def list_all_authors(library_id: str):
    """
    List all authors in a library with their book counts.
    
    Args:
        library_id: The library ID
    """
    authors = await get_all_authors(library_id)
    
    print(f"Authors in library ({len(authors)} total):")
    print("=" * 50)
    
    # Sort by number of books (descending)
    sorted_authors = sorted(
        authors,
        key=lambda a: getattr(a, 'num_books', 0),
        reverse=True
    )
    
    for author in sorted_authors:
        num_books = getattr(author, 'num_books', 0)
        has_image = hasattr(author, 'image_path') and author.image_path
        image_status = "📷" if has_image else "  "
        
        print(f"{image_status} {author.name} ({num_books} books)")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    AUDIOBOOKS_LIBRARY_ID = "d852a24d-c105-4b71-a0ab-5bc5070e49d5"
    
    print("=== List All Authors ===\n")
    asyncio.run(list_all_authors(AUDIOBOOKS_LIBRARY_ID))
    
    print("\n=== Search for Author ===\n")
    author = asyncio.run(search_author(AUDIOBOOKS_LIBRARY_ID, "Asimov"))
    if author:
        print(f"Found: {author.name} (ID: {author.id_})")
    
    print("\n=== Get Author with Books ===\n")
    author, books = asyncio.run(get_author_with_books(AUDIOBOOKS_LIBRARY_ID, "Asimov"))
    if author:
        print(f"Author: {author.name}")
        print(f"Books: {len(books)}")
        for book in books:
            print(f"  - {book['title']}")
    
    print("\n=== Export Authors Without Pictures ===\n")
    asyncio.run(export_authors_without_pictures(AUDIOBOOKS_LIBRARY_ID, "authors_no_pics.json"))

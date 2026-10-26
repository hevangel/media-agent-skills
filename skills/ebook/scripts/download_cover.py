"""
Download book cover images from online sources.
Supports OpenLibrary and Google Books APIs.
"""

import os
import requests
import time
from pathlib import Path
from typing import Optional, Union


def download_cover_openlibrary(isbn: str, save_path: Union[str, Path], size: str = 'L') -> bool:
    """
    Download a book cover from Open Library by ISBN.
    
    Args:
        isbn: ISBN-10 or ISBN-13 of the book
        save_path: Path where the cover image will be saved
        size: Size of the cover - 'S' (small), 'M' (medium), 'L' (large)
        
    Returns:
        True if download was successful
        
    Example:
        download_cover_openlibrary('9780545060394', 'covers/maze_of_bones.jpg')
    """
    # Remove hyphens from ISBN
    isbn = isbn.replace('-', '')
    
    url = f"https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Check if we got a real image (not a 1x1 placeholder)
            if len(response.content) > 1000:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
    except Exception as e:
        print(f"OpenLibrary error: {e}")
    
    return False


def download_cover_google_books(isbn: str, save_path: Union[str, Path]) -> bool:
    """
    Download a book cover from Google Books API by ISBN.
    
    Args:
        isbn: ISBN-10 or ISBN-13 of the book
        save_path: Path where the cover image will be saved
        
    Returns:
        True if download was successful
        
    Example:
        download_cover_google_books('9780545060394', 'covers/maze_of_bones.jpg')
    """
    # Remove hyphens from ISBN
    isbn = isbn.replace('-', '')
    
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('totalItems', 0) > 0:
                items = data.get('items', [])
                if items:
                    volume_info = items[0].get('volumeInfo', {})
                    image_links = volume_info.get('imageLinks', {})
                    
                    # Try to get the largest image available
                    for size in ['extraLarge', 'large', 'medium', 'thumbnail', 'smallThumbnail']:
                        if size in image_links:
                            img_url = image_links[size]
                            # Remove zoom parameter limitations for better quality
                            img_url = img_url.replace('zoom=1', 'zoom=0')
                            
                            img_response = requests.get(img_url, timeout=15)
                            if img_response.status_code == 200 and len(img_response.content) > 1000:
                                save_path = Path(save_path)
                                save_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(save_path, 'wb') as f:
                                    f.write(img_response.content)
                                return True
    except Exception as e:
        print(f"Google Books error: {e}")
    
    return False


def download_cover(
    isbn: str,
    save_path: Union[str, Path],
    sources: list = None
) -> bool:
    """
    Download a book cover, trying multiple sources.
    
    Args:
        isbn: ISBN-10 or ISBN-13 of the book
        save_path: Path where the cover image will be saved
        sources: List of sources to try ('openlibrary', 'google')
                 Defaults to ['openlibrary', 'google']
        
    Returns:
        True if download was successful from any source
        
    Example:
        download_cover('9780545060394', 'covers/book.jpg')
    """
    if sources is None:
        sources = ['openlibrary', 'google']
    
    for source in sources:
        if source == 'openlibrary':
            if download_cover_openlibrary(isbn, save_path):
                return True
        elif source == 'google':
            if download_cover_google_books(isbn, save_path):
                return True
    
    return False


def download_cover_multi_isbn(
    isbns: list,
    save_path: Union[str, Path],
    sources: list = None
) -> Optional[str]:
    """
    Download a book cover by trying multiple ISBNs from multiple sources.
    
    Useful for books with multiple editions (hardcover, paperback, international)
    where some ISBNs may have better cover availability than others.
    
    Args:
        isbns: List of ISBN-10 or ISBN-13 strings to try
        save_path: Path where the cover image will be saved
        sources: List of sources to try ('openlibrary', 'google')
                 Defaults to ['openlibrary', 'google']
        
    Returns:
        String describing the source and ISBN used, or None if all failed
        
    Example:
        # Try multiple ISBNs for the same book
        isbns = ['9780545060394', '0545060397', '9780545060400']
        source = download_cover_multi_isbn(isbns, 'covers/book.jpg')
        if source:
            print(f"Downloaded from: {source}")
    """
    if sources is None:
        sources = ['openlibrary', 'google']
    
    for isbn in isbns:
        for source in sources:
            if source == 'openlibrary':
                if download_cover_openlibrary(isbn, save_path):
                    return f"OpenLibrary (ISBN: {isbn})"
            elif source == 'google':
                if download_cover_google_books(isbn, save_path):
                    return f"Google Books (ISBN: {isbn})"
    
    return None


def download_covers_multi_isbn_batch(
    books: list,
    output_dir: Union[str, Path],
    delay: float = 0.5
) -> dict:
    """
    Download covers for multiple books, each with multiple ISBN options.
    
    Args:
        books: List of dicts with 'isbns' (list) and 'filename' keys
        output_dir: Directory to save covers
        delay: Delay between requests to avoid rate limiting
        
    Returns:
        Dictionary with counts and details:
        {
            'success': n,
            'failed': n, 
            'skipped': n,
            'details': [{'filename': str, 'source': str}, ...]
        }
        
    Example:
        books = [
            {'isbns': ['9780545060394', '0545060397'], 'filename': '01.jpg'},
            {'isbns': ['9780545060417', '9780545060424'], 'filename': '02.jpg'},
        ]
        result = download_covers_multi_isbn_batch(books, 'covers/')
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {'success': 0, 'failed': 0, 'skipped': 0, 'details': []}
    
    for book in books:
        isbns = book.get('isbns', [])
        filename = book.get('filename')
        
        if not isbns or not filename:
            result['skipped'] += 1
            continue
        
        save_path = output_dir / filename
        
        # Skip if already exists
        if save_path.exists():
            print(f"  Skipped (exists): {filename}")
            result['skipped'] += 1
            continue
        
        print(f"  Downloading: {filename} (trying {len(isbns)} ISBNs)...")
        
        source = download_cover_multi_isbn(isbns, save_path)
        if source:
            print(f"    ✓ Downloaded from {source}")
            result['success'] += 1
            result['details'].append({'filename': filename, 'source': source})
        else:
            print(f"    ✗ Failed (tried all ISBNs)")
            result['failed'] += 1
        
        # Rate limiting
        time.sleep(delay)
    
    return result


def download_covers_batch(
    books: list,
    output_dir: Union[str, Path],
    delay: float = 0.5
) -> dict:
    """
    Download covers for multiple books.
    
    Args:
        books: List of dicts with 'isbn' and 'filename' keys
        output_dir: Directory to save covers
        delay: Delay between requests to avoid rate limiting
        
    Returns:
        Dictionary with counts: {'success': n, 'failed': n, 'skipped': n}
        
    Example:
        books = [
            {'isbn': '9780545060394', 'filename': 'maze_of_bones.jpg'},
            {'isbn': '9780545060417', 'filename': 'one_false_note.jpg'},
        ]
        result = download_covers_batch(books, 'covers/')
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {'success': 0, 'failed': 0, 'skipped': 0}
    
    for book in books:
        isbn = book.get('isbn')
        filename = book.get('filename')
        
        if not isbn or not filename:
            result['skipped'] += 1
            continue
        
        save_path = output_dir / filename
        
        # Skip if already exists
        if save_path.exists():
            print(f"  Skipped (exists): {filename}")
            result['skipped'] += 1
            continue
        
        print(f"  Downloading: {filename}...")
        
        if download_cover(isbn, save_path):
            print(f"    ✓ Downloaded")
            result['success'] += 1
        else:
            print(f"    ✗ Failed")
            result['failed'] += 1
        
        # Rate limiting
        time.sleep(delay)
    
    return result


def main():
    """Example: Download covers for The 39 Clues series."""
    from pathlib import Path
    
    # Example: The 39 Clues original series
    books = [
        {'isbn': '9780545060394', 'filename': '01_maze_of_bones.jpg'},
        {'isbn': '9780545060417', 'filename': '02_one_false_note.jpg'},
        {'isbn': '9780545060431', 'filename': '03_sword_thief.jpg'},
        {'isbn': '9780545060455', 'filename': '04_beyond_the_grave.jpg'},
        {'isbn': '9780545060479', 'filename': '05_black_circle.jpg'},
    ]
    
    output_dir = Path(r"/path/to/covers")
    
    print("Downloading covers...")
    result = download_covers_batch(books, output_dir)
    
    print(f"\nResults:")
    print(f"  Success: {result['success']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Skipped: {result['skipped']}")


if __name__ == "__main__":
    main()

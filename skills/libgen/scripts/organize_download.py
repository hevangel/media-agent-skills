"""
Organize a downloaded ebook into the proper folder structure.

Moves downloaded files to Author/Title folder structure.

Usage:
    uv run organize_download.py "downloaded_file.epub" --library "$EBOOK_LIBRARY_PATH"
"""
import argparse
import os
import re
import shutil
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename/folder name.
    
    Args:
        name: The string to sanitize
        
    Returns:
        Sanitized string safe for filesystem use
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Limit length
    return sanitized[:100]


def extract_metadata_from_filename(filename: str) -> dict:
    """
    Try to extract author and title from a libgen-style filename.
    
    Common patterns:
    - "Author Name - Title (Year) - libgen.li.epub"
    - "Author - Title.epub"
    
    Args:
        filename: The filename to parse
        
    Returns:
        Dict with 'author' and 'title' keys
    """
    # Remove extension and common suffixes
    name = Path(filename).stem
    name = re.sub(r'\s*-\s*libgen\.li$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(\d{4}\)\s*$', '', name)  # Remove (Year)
    
    # Try to split by " - "
    if ' - ' in name:
        parts = name.split(' - ', 1)
        return {
            'author': sanitize_filename(parts[0].strip()),
            'title': sanitize_filename(parts[1].strip())
        }
    
    # Fallback: use filename as title, unknown author
    return {
        'author': 'Unknown',
        'title': sanitize_filename(name)
    }


def organize_ebook(
    source_path: str,
    library_path: str,
    author: str | None = None,
    title: str | None = None
) -> str:
    """
    Organize an ebook into Author/Title folder structure.
    
    Args:
        source_path: Path to the downloaded ebook file
        library_path: Base path to the library folder
        author: Author name (optional, extracted from filename if not provided)
        title: Book title (optional, extracted from filename if not provided)
        
    Returns:
        Path to the organized file
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    # Extract metadata from filename if not provided
    if not author or not title:
        metadata = extract_metadata_from_filename(source.name)
        author = author or metadata['author']
        title = title or metadata['title']
    
    # Create destination path: Library/Author/Title/
    dest_dir = Path(library_path) / sanitize_filename(author) / sanitize_filename(title)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Create destination filename: Title - Author.ext
    ext = source.suffix
    dest_filename = f"{sanitize_filename(title)} - {sanitize_filename(author)}{ext}"
    dest_path = dest_dir / dest_filename
    
    # Move the file
    shutil.move(str(source), str(dest_path))
    
    return str(dest_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize a downloaded ebook")
    parser.add_argument("source", help="Path to the downloaded ebook file")
    parser.add_argument("--library", "-l", required=True, help="Base path to the library folder")
    parser.add_argument("--author", "-a", help="Override author name")
    parser.add_argument("--title", "-t", help="Override book title")
    
    args = parser.parse_args()
    
    try:
        dest = organize_ebook(args.source, args.library, args.author, args.title)
        print(f"✓ Organized to: {dest}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)

# EPUB Code Snippets

Python scripts for working with EPUB files - extracting, updating, and managing metadata and covers.

## Overview

This directory contains reusable Python modules for EPUB metadata management. All scripts are designed to work with Calibre Library structures but can be adapted for any EPUB collection.

## Prerequisites

Install required packages:
```bash
uv pip install ebooklib lxml requests
```

## Available Scripts

### 1. extract_metadata.py
**Purpose**: Extract metadata from EPUB files and save to JSON

**Usage**:
```bash
uv run python ebook_organizer/epub_code_snippet/extract_metadata.py
```

**What it does**:
- Recursively scans a directory for EPUB files
- Extracts Dublin Core metadata (title, creator, publisher, etc.)
- Saves results to JSON file for analysis
- Shows progress during extraction

**Key Functions**:
- `extract_epub_metadata(epub_path)` - Extract metadata from single EPUB
- `scan_epub_files(directory)` - Scan directory for EPUBs

### 2. update_metadata.py
**Purpose**: Update EPUB metadata by directly modifying the OPF file

**Usage**:
```bash
uv run python ebook_organizer/epub_code_snippet/update_metadata.py
```

**What it does**:
- Opens EPUB (ZIP archive) and modifies OPF manifest
- Updates Dublin Core metadata fields
- Creates automatic backups (.backup extension)
- Handles single or multiple authors

**Key Functions**:
- `update_epub_metadata(epub_path, new_metadata, create_backup=True)` - Update EPUB metadata
- `extract_opf_metadata(epub_path)` - Extract metadata directly from OPF

**Example**:
```python
from ebook_organizer.epub_code_snippet.update_metadata import update_epub_metadata

# Update single author
update_epub_metadata(
    "book.epub",
    {
        'creator': 'Author Name',
        'publisher': 'Publisher Name'
    }
)

# Update multiple authors
update_epub_metadata(
    "book.epub",
    {
        'title': 'Full Book Title',
        'creator': ['Author 1', 'Author 2', 'Author 3']
    }
)
```

### 3. update_series_metadata.py
**Purpose**: Add or update Calibre-compatible series metadata in EPUB files

**Usage**:
```bash
uv run python ebook_organizer/epub_code_snippet/update_series_metadata.py
```

**What it does**:
- Adds `calibre:series` and `calibre:series_index` metadata
- Compatible with Calibre and Kavita for series organization
- Reads book data from JSON and batch updates EPUBs

**Key Functions**:
- `update_epub_series(epub_path, series_name, series_index)` - Update series info

**Example**:
```python
from ebook_organizer.epub_code_snippet.update_series_metadata import update_epub_series

update_epub_series(
    "book.epub",
    series_name="The Hunger Games",
    series_index=1
)
```

### 4. embed_cover.py
**Purpose**: Embed cover images into EPUB files with proper EPUB2/EPUB3 compatibility

**Usage**:
```bash
uv run python ebook_organizer/epub_code_snippet/embed_cover.py
```

**What it does**:
- Removes existing cover images to prevent conflicts
- Adds new cover image to EPUB archive
- Updates OPF manifest with proper `cover-image` properties
- Supports both EPUB2 and EPUB3 standards

**Key Functions**:
- `embed_cover_image(epub_path, cover_image_path, remove_existing_covers=True)` - Embed a cover
- `get_cover_info(epub_path)` - Get info about existing cover

**Example**:
```python
from ebook_organizer.epub_code_snippet.embed_cover import embed_cover_image, get_cover_info

# Embed a cover (removes old covers first)
embed_cover_image('book.epub', 'cover.jpg')

# Check existing cover
info = get_cover_info('book.epub')
print(f"Cover: {info['filename']} ({info['size']} bytes)")
```

### 5. download_cover.py
**Purpose**: Download book covers from online sources (OpenLibrary, Google Books)

**Usage**:
```bash
uv run python ebook_organizer/epub_code_snippet/download_cover.py
```

**What it does**:
- Downloads covers using ISBN from multiple sources
- Tries OpenLibrary first, then Google Books
- Supports batch downloading with rate limiting

**Key Functions**:
- `download_cover(isbn, save_path)` - Download from any available source
- `download_cover_openlibrary(isbn, save_path)` - Download from OpenLibrary
- `download_cover_google_books(isbn, save_path)` - Download from Google Books
- `download_covers_batch(books, output_dir)` - Batch download multiple covers

**Example**:
```python
from ebook_organizer.epub_code_snippet.download_cover import download_cover, download_covers_batch

# Download single cover
download_cover('9780545060394', 'covers/maze_of_bones.jpg')

# Batch download
books = [
    {'isbn': '9780545060394', 'filename': 'book1.jpg'},
    {'isbn': '9780545060417', 'filename': 'book2.jpg'},
]
download_covers_batch(books, 'covers/')
```

### 6. check_metadata.py
**Purpose**: Analyze extracted metadata to find missing or incomplete information

**Usage**:
```bash
uv run python ebook_organizer/epub_code_snippet/check_metadata.py
```

**What it does**:
- Reads metadata JSON from extract_metadata.py
- Identifies EPUBs missing title, author, or both
- Generates detailed reports grouped by issue type
- Helps prioritize metadata cleanup

**Key Functions**:
- `check_missing_metadata(metadata_json_path)` - Analyze metadata for issues
- `print_missing_metadata_report(results)` - Print formatted report

## Typical Workflows

### Fix Missing Metadata
```bash
# 1. Extract metadata from EPUB collection
uv run python ebook_organizer/epub_code_snippet/extract_metadata.py

# 2. Check for missing metadata
uv run python ebook_organizer/epub_code_snippet/check_metadata.py

# 3. Update EPUBs with missing metadata
python -c "
from ebook_organizer.epub_code_snippet.update_metadata import update_epub_metadata
update_epub_metadata('path/to/book.epub', {'creator': 'Author', 'title': 'Title'})
"
```

### Add Series Information
```python
from ebook_organizer.epub_code_snippet.update_series_metadata import update_epub_series

# Update series for a book
update_epub_series('book.epub', 'Harry Potter', 1)
```

### Download and Embed Covers
```python
from ebook_organizer.epub_code_snippet.download_cover import download_cover
from ebook_organizer.epub_code_snippet.embed_cover import embed_cover_image

# Download cover
if download_cover('9780545060394', 'temp/cover.jpg'):
    # Embed into EPUB
    embed_cover_image('book.epub', 'temp/cover.jpg')
```

### Complete Metadata Fix Pipeline
```python
from ebook_organizer.epub_code_snippet.update_metadata import update_epub_metadata
from ebook_organizer.epub_code_snippet.update_series_metadata import update_epub_series
from ebook_organizer.epub_code_snippet.download_cover import download_cover
from ebook_organizer.epub_code_snippet.embed_cover import embed_cover_image

epub_path = 'book.epub'
isbn = '9780545060394'

# 1. Fix basic metadata
update_epub_metadata(epub_path, {
    'title': 'The Maze of Bones',
    'creator': 'Rick Riordan',
    'publisher': 'Scholastic'
})

# 2. Add series info
update_epub_series(epub_path, 'The 39 Clues', 1)

# 3. Download and embed cover
cover_path = 'temp/cover.jpg'
if download_cover(isbn, cover_path):
    embed_cover_image(epub_path, cover_path)
```

## EPUB Metadata Fields (Dublin Core)

Standard metadata fields:
- `title` - Book title
- `creator` - Author(s) - can be a list
- `publisher` - Publisher name
- `date` - Publication date
- `language` - Language code (e.g., 'en')
- `identifier` - ISBN or other identifiers
- `subject` - Genre/categories/tags
- `description` - Book description
- `rights` - Copyright information
- `contributor` - Contributors (editors, translators)

Calibre extensions:
- `calibre:series` - Series name
- `calibre:series_index` - Position in series

## Notes

- EPUB files are ZIP archives containing XHTML content and an OPF manifest
- Metadata is stored in the OPF file (Package Document)
- Always test metadata updates on a few files before batch processing
- Backups are created automatically when using update_metadata.py
- All temporary output files are saved to `temp/` directory
- Cover images should be JPG or PNG format

## Integration

These scripts work well with:
- **Calibre** - Library management
- **Kavita** - Web-based ebook reader/server (use `scan_library.py` after updates)
- **Custom workflows** - Import functions into your own scripts

## Related Files

- See `ebook_organizer/kavita_code_snippet/` for Kavita API integration
- See `ebook_organizer/kavita.prompt.md` for Kavita server details

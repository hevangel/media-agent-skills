---
name: ebook
description: "Work with EPUB files - extract, update, and manage metadata, download and embed covers, update series info. Use when handling EPUB ebook libraries or metadata."
license: MIT
compatibility: Requires Python 3.13+, uv, ebooklib, and lxml
---

# EPUB Manager

## Configuration

Library paths are loaded from the `.env` file in the workspace root.

```env
EBOOK_LIBRARY_PATH=/path/to/ebook/library
```

You can configure multiple library paths as needed. The default structure follows Calibre conventions:
`$EBOOK_LIBRARY_PATH/Author Name/Book Title (ID)/book.epub`

## Reference

- Code Snippets: `scripts/`
- Code Snippet README: `scripts/README.md`
- Kavita integration: See the `kavita` skill

## Available Scripts

| Script | Purpose |
|--------|---------|
| `extract_metadata.py` | Extract metadata from EPUBs to JSON |
| `update_metadata.py` | Update Dublin Core metadata (title, author, publisher) |
| `update_series_metadata.py` | Add Calibre-compatible series info |
| `embed_cover.py` | Embed cover images into EPUBs |
| `download_cover.py` | Download covers from OpenLibrary/Google Books (supports multiple ISBNs) |
| `check_metadata.py` | Find EPUBs with missing metadata |

## Common Tasks

### Extract Metadata
Extract metadata from all EPUB files in a directory recursively and save to JSON.

### Check for Missing Metadata
Analyze extracted metadata to find EPUBs missing title, author, or other key fields.

### Fetch Missing Metadata
- Use `fetch-ebook-metadata` from Calibre: https://manual.calibre-ebook.com/generated/en/fetch-ebook-metadata.html
- Use [openlibrary-client](https://pypi.org/project/openlibrary-client/) for additional metadata.

### Update Metadata
Modify EPUB metadata (title, author, publisher) by editing the OPF file within the EPUB.

### Update Series Info
Add Calibre-compatible series metadata (`calibre:series` and `calibre:series_index`).

## EPUB Metadata Fields (Dublin Core)

- `title`, `creator`, `publisher`, `date`, `language`, `identifier` (ISBN)
- `subject` (genres/tags), `description`, `rights`, `contributor`

## EPUB Structure

EPUB files are ZIP archives containing:
- `mimetype` - Must be first file, uncompressed
- `META-INF/container.xml` - Points to OPF file
- `content.opf` - Package document with metadata
- `OEBPS/` - Content directory with XHTML, CSS, images

## Code Examples

### Extract Metadata

```python
from skills.ebook.scripts.extract_metadata import extract_epub_metadata, scan_epub_files
from pathlib import Path

metadata = extract_epub_metadata(Path("book.epub"))
all_metadata = scan_epub_files(Path(os.environ["EBOOK_LIBRARY_PATH"]))
```

### Update Metadata

```python
from skills.ebook.scripts.update_metadata import update_epub_metadata

update_epub_metadata("book.epub", {
    'creator': ['Author 1', 'Author 2'],
    'publisher': 'Publisher Name'
})
```

### Download and Embed Cover

```python
from skills.ebook.scripts.download_cover import download_cover_multi_isbn
from skills.ebook.scripts.embed_cover import embed_cover_image

isbns = ['9780545060394', '0545060397']
source = download_cover_multi_isbn(isbns, 'temp/cover.jpg')
if source:
    embed_cover_image('book.epub', 'temp/cover.jpg')
```

### Update Series

```python
from skills.ebook.scripts.update_series_metadata import update_epub_series
update_epub_series('book.epub', 'Series Name', 1)
```

## Common Issues

- **Cover Not Showing**: Multiple cover images in EPUB. Use `embed_cover_image()` with `remove_existing_covers=True`.
- **Series Not Detected**: Use `update_epub_series()` to add Calibre series metadata.
- **Changes Not in Kavita**: Trigger rescan with force mode via the Kavita skill.

## Notes

- Use `uv` as the Python package manager.
- Temporary files go in `$WORKSPACE_PATH/temp/`.
- Backups created automatically with `.backup` extension.
- Always test on a few files before batch processing.

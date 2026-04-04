---
name: libgen
description: "Search and download ebooks from Library Genesis (LibGen). Use when the user needs to find or download ebooks, EPUBs, or PDFs from LibGen."
license: MIT
compatibility: Requires Python 3.13+, uv, libgen-api-enhanced, and playwright for browser-based downloads
---

# LibGen Ebook Downloader

## Configuration

Library paths are loaded from the `.env` file in the workspace root.

```env
EBOOK_LIBRARY_PATH=/path/to/ebook/library
```

## Reference

- Code Snippets: `scripts/`
- Code Snippet README: `scripts/README.md`
- EPUB integration: See the `ebook` skill

## Python Package

- [libgen-api-enhanced](https://pypi.org/project/libgen-api-enhanced/): Python wrapper for the LibGen API

## Available Scripts

| Script | Purpose |
|--------|---------|
| `search_books.py` | Search for books by title, author, format |
| `download_book.py` | Get download URLs by MD5 hash |
| `playwright_download.py` | Download using Playwright browser automation |
| `organize_download.py` | Organize to Author/Title folder structure |

## Common Tasks

### Search for a Book

```python
from libgen_api_enhanced import LibgenSearch

search = LibgenSearch()
results = search.search_title("Wrath of the Triple Goddess")
for r in results[:5]:
    print(f"{r.title} by {r.author} - {r.extension} - {r.size}")
```

### Download with Playwright

```python
from skills.libgen.scripts.playwright_download import download_from_libgen, search_and_download

filepath = search_and_download(
    title="Wrath of the Triple Goddess",
    output_dir="temp/libgen_downloads",
    author="Rick Riordan",
    format="epub"
)
```

### Alternative Download Sources

If libgen.li fails:
- **Anna's Archive**: `https://en.annas-archive.org/md5/<MD5_HASH>`
- **Libgen.rs**: `https://libgen.rs/fiction/<MD5_HASH>`

## Folder Organization

Downloaded ebooks should be organized into:
```
$EBOOK_LIBRARY_PATH/
  Author Name/
    Book Title/
      Book Title - Author Name.epub
```

## Troubleshooting

- **Connection Reset / SSL Errors**: ISP blocking — enable VPN and retry.
- **CAPTCHA**: Use libgen.li directly instead of Anna's Archive.
- **Download Corrupted**: Use Playwright browser automation instead of direct HTTP requests.

## Notes

- Download to `$WORKSPACE_PATH/temp/libgen_downloads/` first, then organize.
- Respect rate limits: 1 request/~2 seconds, add jitter, back off on 503/429.
- Always test on a few files before batch processing.

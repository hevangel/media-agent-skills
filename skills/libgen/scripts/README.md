# Libgen Code Snippets

Reusable Python scripts for searching and downloading ebooks from Library Genesis.

## Scripts

| Script | Purpose |
|--------|---------|
| `search_books.py` | Search for books by title, author, and format |
| `download_book.py` | Get download URLs for a book by MD5 hash |
| `playwright_download.py` | Download books using Playwright browser automation |
| `organize_download.py` | Organize downloaded files into Author/Title structure |

## Requirements

Install dependencies with:
```bash
uv pip install libgen-api-enhanced requests playwright
playwright install chromium
```

## Usage

### Search for Books

```bash
# Search by title
uv run search_books.py "Wrath of the Triple Goddess"

# Search with author filter
uv run search_books.py "Wrath of the Triple Goddess" --author "Rick Riordan"

# Search for specific format
uv run search_books.py "Wrath of the Triple Goddess" --format epub
```

### Download a Book (Playwright Script)

Use the Playwright script for reliable automated downloads:

```bash
# Download by MD5 hash
uv run playwright_download.py 0e5d19a33afebc900650bb582ad4df6a --output "./downloads"

# Headless mode (no browser window)
uv run playwright_download.py 0e5d19a33afebc900650bb582ad4df6a --output "./downloads" --headless
```

### Download via MCP Playwright (Agent Mode)

When using the AI agent with Playwright MCP tools:

1. Search for the book to get its MD5 hash
2. Navigate to `https://libgen.li/ads.php?md5=<MD5_HASH>`
3. Click the "GET" button at the top
4. If connection fails, enable VPN and try again

### Manual Download URLs

```bash
# Get download URLs for manual download
uv run download_book.py 0e5d19a33afebc900650bb582ad4df6a
```

### Organize Downloaded Files

```bash
# Organize a downloaded file into Author/Title structure
uv run organize_download.py "downloaded_book.epub" --library "E:\ebook\Youth Novels"

# Override author/title if auto-detection fails
uv run organize_download.py "book.epub" --library "E:\ebook\Youth Novels" \
    --author "Rick Riordan" --title "Wrath of the Triple Goddess"
```

## Python API

### Search for Books

```python
from search_books import search_books

# Search with filters
results = search_books(
    title="Wrath of the Triple Goddess",
    author="Rick Riordan",
    format="epub",
    limit=5
)

for book in results:
    print(f"{book.title} - {book.author}")
    print(f"  MD5: {book.md5}")
    print(f"  Format: {book.extension}, Size: {book.size}")
```

### Download with Playwright

```python
from playwright_download import download_from_libgen, search_and_download

# Download by MD5 hash
filepath = download_from_libgen(
    md5="0e5d19a33afebc900650bb582ad4df6a",
    output_dir="./downloads",
    headless=False  # Set True for background downloads
)

# Search and download in one step
filepath = search_and_download(
    title="Wrath of the Triple Goddess",
    output_dir="./downloads",
    author="Rick Riordan",
    format="epub"
)
```

### Organize Downloads

```python
from organize_download import organize_ebook

# Auto-detect author/title from filename
dest = organize_ebook(
    source_path="Rick Riordan - Wrath of the Triple Goddess (2024) - libgen.li.epub",
    library_path=os.environ["EBOOK_LIBRARY_PATH"]
)
print(f"Organized to: {dest}")
# Output: E:\ebook\Youth Novels\Rick Riordan\Wrath of the Triple Goddess\Wrath of the Triple Goddess - Rick Riordan.epub

# With explicit author/title
dest = organize_ebook(
    source_path="downloaded_book.epub",
    library_path=os.environ["EBOOK_LIBRARY_PATH"],
    author="Rick Riordan",
    title="Wrath of the Triple Goddess"
)
```

## Workflow Example

Complete workflow to download and organize a book:

```python
from playwright_download import download_from_libgen
from search_books import search_books
from organize_download import organize_ebook

# 1. Search for the book
results = search_books("Wrath of the Triple Goddess", author="Rick Riordan", format="epub")
if not results:
    print("Book not found")
    exit(1)

book = results[0]
print(f"Found: {book.title}")
print(f"MD5: {book.md5}")

# 2. Download using Playwright
downloaded_file = download_from_libgen(
    md5=book.md5,
    output_dir="./temp_downloads",
    headless=False
)

if downloaded_file:
    # 3. Organize to library
    dest = organize_ebook(
        source_path=downloaded_file,
        library_path=os.environ["EBOOK_LIBRARY_PATH"],
        author=book.author,
        title=book.title
    )
    print(f"Organized to: {dest}")
```

## Troubleshooting

### Connection Reset / SSL Errors
- Libgen servers may be blocked by your ISP
- **Solution**: Use a VPN

### Download Starts but File is Corrupted
- Anti-bot measures may serve fake content
- **Solution**: Use browser automation instead of direct HTTP requests

### Book Not Found
- Try different search terms
- Check if the book is available on libgen at all
- Try searching on Anna's Archive: `https://en.annas-archive.org/search?q=<title>`

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

### Agent-mode browser download: Webwright (preferred), Playwright CLI (fallback)

When an agent should drive the browser from the terminal (not Playwright MCP), use this order:

1. **[Webwright](https://github.com/microsoft/Webwright)** — Microsoft’s terminal-native harness: a coding-agent loop that writes Playwright Python scripts, saves trajectories and screenshots, and fits **multi-step** flows (forms, mirrors, retries). **Install it through your agent’s plugin marketplace** (no Git clone and no `pip install -e .` from source):

   - **Claude Code:** `/plugin marketplace add microsoft/Webwright` then `/plugin install webwright@webwright` — use `/webwright:run` / `/webwright:craft` or plain English; see the [Webwright README](https://github.com/microsoft/Webwright/blob/main/README.md).
   - **OpenAI Codex:** `codex plugin marketplace add microsoft/Webwright`, then install **webwright** from the plugins UI; invoke with `@webwright` or natural language (same README).
   - **OpenClaw, Hermes, etc.:** follow the “Install” sections in that README (`openclaw plugins install …`, symlink `skills/webwright`, …).

   Example (after the plugin is installed — adjust for your host’s slash-command style):

   ```text
   /webwright:run Open https://libgen.li/ads.php?md5=<MD5_HASH>, use the top GET link to finish the download, and save the file under temp/libgen_downloads.
   ```

   Configuration and API keys follow **upstream Webwright** docs (the plugin bundles the harness; you do not need to vendor this repo’s source).

2. **[Playwright CLI](https://www.npmjs.com/package/@playwright/cli)** (`playwright-cli`) — **fallback** when Webwright is not available, or you only need a **few deterministic** steps (`open` → `snapshot` → `click`). Token-efficient micro-commands; no agent loop.

**Playwright CLI** (Node.js 18+):

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
# Optional: bundled agent skills
playwright-cli install --skills
# Or: npx @playwright/cli@latest --help
```

Typical LibGen flow with **playwright-cli** only:

```bash
playwright-cli open "https://libgen.li/ads.php?md5=<MD5_HASH>"
playwright-cli snapshot
playwright-cli click <ref>   # ref for the top "GET" link from the snapshot
```

If the download opens a new tab: `playwright-cli tab-list` / `playwright-cli tab-select <index>`. If the connection fails, use a VPN and retry.

Prefer **`playwright_download.py`** when automation should stay inside this repo’s **Python/uv** stack without either harness above.

> **Note:** The PyPI project named [`webwright`](https://pypi.org/project/webwright/) is **not** Microsoft Webwright. Prefer the **plugin install** above; do not `pip install webwright` expecting Microsoft’s harness.

### Manual Download URLs

```bash
# Get download URLs for manual download
uv run download_book.py 0e5d19a33afebc900650bb582ad4df6a
```

### Organize Downloaded Files

```bash
# Organize a downloaded file into Author/Title structure
uv run organize_download.py "downloaded_book.epub" --library "/path/to/ebook/library"

# Override author/title if auto-detection fails
uv run organize_download.py "book.epub" --library "/path/to/ebook/library" \
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
# Output: /path/to/ebook/library/Rick Riordan/Wrath of the Triple Goddess/Wrath of the Triple Goddess - Rick Riordan.epub

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

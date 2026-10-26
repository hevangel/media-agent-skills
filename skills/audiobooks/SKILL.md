---
name: audiobooks
description: "Manage audiobooks: download missing covers, organize metadata, embed cover art, and download from AudiobookBay. Use when working with audiobook libraries, cover images, or AudiobookBay searches."
license: MIT
compatibility: Requires Python 3.13+, uv, mutagen, and playwright
---

# Audiobook Manager

## Core Capabilities

1. **Audiobook Organizer**: Download missing covers, scan library, and embed metadata.
2. **AudiobookBay Downloader**: Search and download audiobooks from AudiobookBay.

## Configuration

All settings are loaded from the `.env` file in the workspace root.

```env
# AudiobookBay credentials
AUDIOBOOKBAY_URL=https://audiobookbay.nl/
AUDIOBOOKBAY_USERNAME=your_username
AUDIOBOOKBAY_PASSWORD=your_password

# Library path
AUDIOBOOKS_PATH=/path/to/audiobooks
```

## Library Information

- **Main Library**: Configured via `AUDIOBOOKS_PATH` in `.env`
- **Structure**: `$AUDIOBOOKS_PATH/Author Name/Audiobook Title/`

## Reference

- Core Code Snippets: `scripts/core/`
- Utility Code Snippets: `scripts/utils/`
- CLI Tool: `scripts/cli/`

## Workflow: Identify & Fix Missing Covers

1. **Scan**: List all audiobooks missing covers (`cover.jpg`, `folder.jpg`, embedded art).
2. **Search**: Find cover art on Audible (start with audible.ca), Amazon, or Google Images.
3. **Download & Organize**: Save as `cover.jpg` in the book's folder.
4. **Embed**: Embed metadata and cover image into the audio files (`.m4b`, `.mp3`, etc.).

## Usage Examples (CLI)

```bash
# Scan library for missing covers
uv run python skills/audiobooks/scripts/cli/cover_manager.py scan --report

# List missing covers
uv run python skills/audiobooks/scripts/cli/cover_manager.py list --by-author

# Process a specific book (download & embed)
uv run python skills/audiobooks/scripts/cli/cover_manager.py process -i <INDEX> -u "<IMAGE_URL>"

# Embed existing cover into files
uv run python skills/audiobooks/scripts/cli/cover_manager.py embed -c cover.jpg -a "$AUDIOBOOKS_PATH/Author/Title"
```

## Python Module Structure

- `core/scanner.py`: Library scanning logic.
- `core/embedder.py`: Cover embedding (mutagen).
- `core/downloader.py`: Cover downloading.
- `utils/image_handler.py`: Image conversion.
- `utils/audio_handler.py`: Audio file detection.

---

## AudiobookBay Downloader

### Reference

- Code Snippets: `scripts/audiobookbay/`

### Usage Example

```python
from skills.audiobooks.scripts.audiobookbay.search import search, enrich_with_magnets
from skills.audiobooks.scripts.audiobookbay.client import AudiobookbayClient

# Simple search
results = search("Arifureta", max_pages=2)

# Get magnet links for all results
results = enrich_with_magnets(results)

# Print results
for result in results:
    print(result.title, result.magnet_link)
```

### Important Notes for AudiobookBay

- Download ebooks to `$WORKSPACE_PATH/temp/audiobookbay_downloads/` initially.
- After download, organize to the appropriate library folder.
- Respect rate limits (1 request/2s).

---

## General Notes

- Use `uv` as the Python package manager.
- Create temporary files in `$WORKSPACE_PATH/temp/`.
- Handle errors gracefully (missing directories, network issues).
- Backup original files before modifying metadata if requested.

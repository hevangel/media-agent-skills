---
name: kavita
description: "Interact with the Kavita reading server API to manage ebook/manga libraries, list series, get metadata, and trigger library rescans. Use when working with Kavita servers."
license: MIT
compatibility: Requires Python 3.13+, uv, and requests
---

# Kavita API

## Configuration

All settings are loaded from the `.env` file in the workspace root.

```env
KAVITA_HOST=http://localhost/kavita
KAVITA_USERNAME=your_username
KAVITA_PASSWORD=your_password
KAVITA_API_KEY=your_api_key
```

## Reference

- Kavita API documentation: https://www.kavitareader.com/docs/api/
- Code Snippets: `scripts/`

**Note:** Scripts use `config.py` to load credentials from `.env`.

## Available Scripts

| Script | Purpose |
|--------|---------|
| `config.py` | Configuration loader (from `.env`) |
| `list_libraries.py` | List all libraries (JWT auth demo) |
| `get_library_books.py` | Get all books/series from a library |
| `get_series_metadata.py` | Detailed metadata (authors, genres, tags) |
| `dump_library_to_json.py` | Export all books with full metadata |
| `scan_library.py` | Trigger library rescan (supports force mode) |

## Key Patterns

### JWT Authentication

```python
url = f"{SERVER_URL}/api/account/login"
payload = {"username": USERNAME, "password": PASSWORD}
response = requests.post(url, json=payload, timeout=10)
token = response.json().get('token')
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

### Important: Library Filtering

`libraryId` must be a **query parameter**, not in the request body:

```python
# Correct
params = {"libraryId": library_id, "PageNumber": 0, "PageSize": 0}
response = requests.post(f"{SERVER_URL}/api/series/all", headers=headers, params=params, json={})

# Wrong - returns ALL books from ALL libraries
response = requests.post(f"{SERVER_URL}/api/series/all", headers=headers, json={"libraryIds": [library_id]})
```

## Usage Examples

```bash
cd skills/kavita/scripts
uv run python list_libraries.py
uv run python get_library_books.py
uv run python dump_library_to_json.py
uv run python scan_library.py
```

## Notes

- Temporary files go in `$WORKSPACE_PATH/temp/`.

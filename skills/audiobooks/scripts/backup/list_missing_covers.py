"""List all audiobooks missing covers."""

import json

with open('audiobook_scan_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

missing = [ab for ab in data['audiobooks'] if not ab['has_cover'] and not ab['has_embedded_cover']]

print(f'Total audiobooks missing covers: {len(missing)}\n')

for i, ab in enumerate(missing, 1):
    print(f"{i}. {ab['author']} - {ab['title']}")
    print(f"   Path: {ab['path']}")
    print()

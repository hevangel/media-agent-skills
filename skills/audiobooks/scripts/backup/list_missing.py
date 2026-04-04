import json

with open('audiobook_scan_results.json', 'r') as f:
    data = json.load(f)

missing = [b for b in data['audiobooks'] if not b['has_cover'] and not b['has_embedded_cover']]

print(f"Found {len(missing)} audiobooks without any covers:\n")
for i, b in enumerate(missing):
    print(f"{i+1}. {b['author']} - {b['title']}")
    print(f"   Path: {b['path']}")
    print()

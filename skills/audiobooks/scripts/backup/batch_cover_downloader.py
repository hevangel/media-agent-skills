"""
Batch Audible Cover Downloader
Uses DuckDuckGo search to find Audible pages and download covers.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(__file__))

from audible_cover_downloader import AudibleCoverDownloader, load_missing_audiobooks


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║        BATCH AUDIBLE COVER DOWNLOADER                              ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    missing = load_missing_audiobooks()
    print(f"\nFound {len(missing)} audiobooks missing covers")
    
    print("\n" + "="*70)
    print("AUDIOBOOKS NEEDING COVERS:")
    print("="*70 + "\n")
    
    # List all missing audiobooks with search queries
    for i, audiobook in enumerate(missing, 1):
        author = audiobook['author']
        title = audiobook['title']
        query = f'"{author}" "{title}" audiobook audible'
        print(f"{i:2}. {author} - {title}")
        print(f"    Search: {query}\n")
    
    print("="*70)


if __name__ == "__main__":
    main()

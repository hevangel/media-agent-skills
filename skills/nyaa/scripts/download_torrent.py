"""
Download a torrent from nyaa.si by adding it to qBittorrent

Usage:
    uv run python skills/nyaa/scripts/download_torrent.py "Frieren" --save-path "./downloads"
    uv run python skills/nyaa/code_snippet/download_torrent.py "Frieren" --index 0 --trusted
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from nyaapy.nyaasi.nyaa import Nyaa
from qbittorrent_skill.code_snippet.qbittorrent_client import get_client, add_magnet


def search_and_download(
    keyword: str,
    save_path: str,
    index: int = 0,
    category: int = 1,
    subcategory: int = 2,
    trusted_only: bool = True
) -> bool:
    """
    Search for an anime and add the selected result to qBittorrent
    
    Args:
        keyword: Search term
        save_path: Path to save the downloaded files
        index: Index of the search result to download (0 = first result)
        category: Category ID (1=Anime)
        subcategory: Subcategory ID (2=English-translated)
        trusted_only: Only search trusted uploads
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Searching nyaa.si for: {keyword}")
    
    filters = 2 if trusted_only else 0
    
    results = Nyaa.search(
        keyword=keyword,
        category=category,
        subcategory=subcategory,
        filters=filters
    )
    
    if not results:
        print("No results found")
        return False
    
    print(f"Found {len(results)} results")
    
    if index >= len(results):
        print(f"Index {index} out of range. Max index: {len(results) - 1}")
        return False
    
    selected = results[index]
    print(f"\nSelected: {selected.name}")
    print(f"  Size: {selected.size}")
    print(f"  Seeders: {selected.seeders}")
    
    if not hasattr(selected, 'magnet') or not selected.magnet:
        print("Error: No magnet link available")
        return False
    
    # Connect to qBittorrent and add torrent
    print(f"\nAdding to qBittorrent...")
    print(f"  Save path: {save_path}")
    
    try:
        client = get_client()
        add_magnet(client, selected.magnet, save_path=save_path)
        print("Successfully added torrent to qBittorrent!")
        return True
    except Exception as e:
        print(f"Error adding torrent: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Search nyaa.si and add torrent to qBittorrent"
    )
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument("--save-path", "-o", required=True,
                        help="Path to save downloaded files")
    parser.add_argument("--index", "-i", type=int, default=0,
                        help="Index of search result to download (default: 0)")
    parser.add_argument("--category", "-c", type=int, default=1,
                        help="Category (1=Anime)")
    parser.add_argument("--subcategory", "-s", type=int, default=2,
                        help="Subcategory (2=English-translated)")
    parser.add_argument("--trusted", "-t", action="store_true", default=True,
                        help="Trusted uploads only (default)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Include non-trusted uploads")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List results without downloading")
    
    args = parser.parse_args()
    
    trusted_only = not args.all
    
    if args.list:
        # Just list results
        filters = 2 if trusted_only else 0
        results = Nyaa.search(
            keyword=args.keyword,
            category=args.category,
            subcategory=args.subcategory,
            filters=filters
        )
        
        print(f"Found {len(results)} results:\n")
        for i, r in enumerate(results[:20]):
            print(f"[{i}] {r.name}")
            print(f"    Size: {r.size} | Seeders: {r.seeders}")
        return
    
    success = search_and_download(
        keyword=args.keyword,
        save_path=args.save_path,
        index=args.index,
        category=args.category,
        subcategory=args.subcategory,
        trusted_only=trusted_only
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

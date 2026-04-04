"""
Search for anime torrents on nyaa.si

Usage:
    uv run python skills/nyaa/code_snippet/search_anime.py "Frieren"
    uv run python skills/nyaa/code_snippet/search_anime.py "Frieren" --category 1 --subcategory 2 --trusted
"""

import argparse
from nyaapy.nyaasi.nyaa import Nyaa


def search_anime(
    keyword: str,
    category: int = 1,
    subcategory: int = 0,
    filters: int = 0,
    page: int = 0,
    limit: int = 20
) -> list:
    """
    Search for anime torrents on nyaa.si
    
    Args:
        keyword: Search term
        category: Category ID (1=Anime, 2=Audio, 3=Literature, etc.)
        subcategory: Subcategory ID (0=All, 2=English-translated for Anime)
        filters: Filter type (0=None, 1=No remakes, 2=Trusted only)
        page: Page number (0-1000)
        limit: Maximum results to return
        
    Returns:
        List of torrent results
    """
    print(f"Searching nyaa.si for: {keyword}")
    print(f"  Category: {category}, Subcategory: {subcategory}, Filter: {filters}")
    
    results = Nyaa.search(
        keyword=keyword,
        category=category,
        subcategory=subcategory,
        filters=filters,
        page=page
    )
    
    print(f"Found {len(results)} results")
    return results[:limit]


def print_results(results: list) -> None:
    """Print search results in a formatted way"""
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r.name}")
        print(f"    Category: {r.category}")
        print(f"    Size: {r.size} | Seeders: {r.seeders} | Leechers: {r.leechers}")
        print(f"    Date: {r.date}")
        print(f"    URL: {r.url}")
        # Only show first 80 chars of magnet
        if hasattr(r, 'magnet') and r.magnet:
            print(f"    Magnet: {r.magnet[:80]}...")


def main():
    parser = argparse.ArgumentParser(description="Search nyaa.si for anime torrents")
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument("--category", "-c", type=int, default=1, 
                        help="Category (1=Anime, 2=Audio, 3=Literature)")
    parser.add_argument("--subcategory", "-s", type=int, default=0,
                        help="Subcategory (0=All, 2=English-translated)")
    parser.add_argument("--trusted", "-t", action="store_true",
                        help="Show trusted uploads only")
    parser.add_argument("--no-remakes", action="store_true",
                        help="Exclude remakes")
    parser.add_argument("--limit", "-l", type=int, default=20,
                        help="Maximum results to show")
    parser.add_argument("--page", "-p", type=int, default=0,
                        help="Page number")
    
    args = parser.parse_args()
    
    # Determine filter
    filters = 0
    if args.trusted:
        filters = 2
    elif args.no_remakes:
        filters = 1
    
    results = search_anime(
        keyword=args.keyword,
        category=args.category,
        subcategory=args.subcategory,
        filters=filters,
        page=args.page,
        limit=args.limit
    )
    
    print_results(results)
    
    return results


if __name__ == "__main__":
    main()

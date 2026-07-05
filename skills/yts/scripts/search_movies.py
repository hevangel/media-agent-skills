"""
Search for movies on YTS (YIFY-style releases).

Usage:
    uv run python skills/yts/scripts/search_movies.py "Inception"
    uv run python skills/yts/scripts/search_movies.py "Dune" --quality 1080p --min-rating 7
    uv run python skills/yts/scripts/search_movies.py --genre sci-fi --sort seeds --limit 10
"""

import argparse
import os
import requests
from urllib.parse import quote


def _yts_api_base_candidates() -> list[str]:
    """Ordered list of API base URLs (no trailing slash)."""
    env = os.environ.get("YTS_API_BASE", "").strip().rstrip("/")
    if env:
        return [env]
    return [
        "https://ytz.mx/api/v2",
        "https://yts.lt/api/v2",
        "https://yts.mx/api/v2",
    ]

# Trackers for building magnet links
TRACKERS = [
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.openbittorrent.com:80",
    "udp://tracker.coppersurfer.tk:6969",
    "udp://glotorrents.pw:6969/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://p4p.arenabg.com:1337",
    "udp://tracker.leechers-paradise.org:6969",
]


def build_magnet(torrent_hash: str, name: str) -> str:
    """Build a magnet link from hash and name"""
    encoded_name = quote(name)
    tracker_str = "&tr=".join(TRACKERS)
    return f"magnet:?xt=urn:btih:{torrent_hash}&dn={encoded_name}&tr={tracker_str}"


def search_movies(
    query: str = None,
    quality: str = None,
    minimum_rating: int = 0,
    genre: str = None,
    sort_by: str = "date_added",
    order_by: str = "desc",
    limit: int = 20,
    page: int = 1
) -> list:
    """
    Search for movies on YTS
    
    Args:
        query: Search term (movie title, IMDb code, actor/director)
        quality: Video quality (720p, 1080p, 2160p, 3D)
        minimum_rating: Minimum IMDb rating (0-9)
        genre: Movie genre
        sort_by: Sort field (title, year, rating, peers, seeds, download_count, date_added)
        order_by: Sort order (asc, desc)
        limit: Results per page (1-50)
        page: Page number
        
    Returns:
        List of movie dictionaries
    """
    print(f"Searching YTS for movies (API candidates: {_yts_api_base_candidates()})...")
    if query:
        print(f"  Query: {query}")
    if quality:
        print(f"  Quality: {quality}")
    if genre:
        print(f"  Genre: {genre}")
    if minimum_rating > 0:
        print(f"  Min Rating: {minimum_rating}")
    
    params = {
        "limit": limit,
        "page": page,
        "sort_by": sort_by,
        "order_by": order_by,
    }
    
    if query:
        params["query_term"] = query
    if quality:
        params["quality"] = quality
    if minimum_rating > 0:
        params["minimum_rating"] = minimum_rating
    if genre:
        params["genre"] = genre
    
    bases = _yts_api_base_candidates()
    last_error: Exception | None = None
    for base in bases:
        try:
            response = requests.get(f"{base}/list_movies.json", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            last_error = e
            print(f"[progress] API attempt failed for {base}: {e}")
            continue

        if data["status"] != "ok":
            print(f"API Error ({base}): {data.get('status_message', 'Unknown error')}")
            return []

        movies = data.get("data", {}).get("movies", [])
        movie_count = data.get("data", {}).get("movie_count", 0)
        print(f"Found {movie_count} total movies, showing {len(movies)} (via {base})")
        return movies

    print(f"Request error: {last_error}")
    return []


def print_results(movies: list, show_magnets: bool = False) -> None:
    """Print search results in a formatted way"""
    for i, movie in enumerate(movies, 1):
        print(f"\n[{i}] {movie['title']} ({movie['year']})")
        print(f"    IMDb: {movie.get('rating', 'N/A')} | Runtime: {movie.get('runtime', 'N/A')} min")
        print(f"    Genres: {', '.join(movie.get('genres', []))}")
        print(f"    URL: {movie.get('url', 'N/A')}")
        
        torrents = movie.get("torrents", [])
        if torrents:
            print("    Torrents:")
            for t in torrents:
                quality = t.get("quality", "N/A")
                size = t.get("size", "N/A")
                seeds = t.get("seeds", 0)
                peers = t.get("peers", 0)
                print(f"      - {quality}: {size} | Seeds: {seeds} | Peers: {peers}")
                
                if show_magnets:
                    magnet = build_magnet(t.get("hash", ""), movie["title"])
                    print(f"        Magnet: {magnet[:80]}...")


def main():
    parser = argparse.ArgumentParser(description="Search YTS for movie torrents")
    parser.add_argument("query", nargs="?", help="Search query (movie title, IMDb code, actor)")
    parser.add_argument("--quality", "-q", choices=["720p", "1080p", "2160p", "3D"],
                        help="Filter by quality")
    parser.add_argument("--min-rating", "-r", type=int, default=0,
                        help="Minimum IMDb rating (0-9)")
    parser.add_argument("--genre", "-g", help="Filter by genre (action, comedy, drama, etc.)")
    parser.add_argument("--sort", "-s", default="date_added",
                        choices=["title", "year", "rating", "peers", "seeds", "download_count", "date_added"],
                        help="Sort by field")
    parser.add_argument("--order", "-o", default="desc", choices=["asc", "desc"],
                        help="Sort order")
    parser.add_argument("--limit", "-l", type=int, default=20,
                        help="Maximum results (1-50)")
    parser.add_argument("--page", "-p", type=int, default=1,
                        help="Page number")
    parser.add_argument("--magnets", "-m", action="store_true",
                        help="Show magnet links")
    
    args = parser.parse_args()
    
    movies = search_movies(
        query=args.query,
        quality=args.quality,
        minimum_rating=args.min_rating,
        genre=args.genre,
        sort_by=args.sort,
        order_by=args.order,
        limit=args.limit,
        page=args.page
    )
    
    print_results(movies, show_magnets=args.magnets)
    
    return movies


if __name__ == "__main__":
    main()

"""
Download a movie from YTS/YIFY by adding it to qBittorrent

Usage:
    uv run python skills/yify/scripts/download_movie.py "Inception" --save-path "./downloads"
    uv run python skills/yify/scripts/download_movie.py "Dune" --quality 1080p --save-path "./downloads"
    uv run python skills/yify/scripts/download_movie.py "Oppenheimer" --index 0 --quality 2160p -o "./downloads"
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import quote

import requests

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from qbittorrent_skill.code_snippet.qbittorrent_client import get_client, add_magnet


# YTS API base URL
YTS_API_BASE = "https://yts.mx/api/v2"

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


def search_movies(query: str, quality: str = None, limit: int = 10) -> list:
    """Search for movies on YTS"""
    params = {
        "query_term": query,
        "limit": limit,
        "sort_by": "seeds",
        "order_by": "desc",
    }
    
    if quality:
        params["quality"] = quality
    
    try:
        response = requests.get(f"{YTS_API_BASE}/list_movies.json", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "ok":
            return []
        
        return data.get("data", {}).get("movies", [])
        
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return []


def search_and_download(
    query: str,
    save_path: str,
    index: int = 0,
    quality: str = "1080p"
) -> bool:
    """
    Search for a movie and add the selected result to qBittorrent
    
    Args:
        query: Search term
        save_path: Path to save the downloaded files
        index: Index of the search result to download (0 = first result)
        quality: Preferred quality (720p, 1080p, 2160p)
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Searching YTS for: {query}")
    
    movies = search_movies(query)
    
    if not movies:
        print("No movies found")
        return False
    
    print(f"Found {len(movies)} movies")
    
    if index >= len(movies):
        print(f"Index {index} out of range. Max index: {len(movies) - 1}")
        return False
    
    movie = movies[index]
    print(f"\nSelected: {movie['title']} ({movie['year']})")
    print(f"  IMDb Rating: {movie.get('rating', 'N/A')}")
    print(f"  Genres: {', '.join(movie.get('genres', []))}")
    
    torrents = movie.get("torrents", [])
    if not torrents:
        print("Error: No torrents available for this movie")
        return False
    
    # Find the preferred quality torrent
    selected_torrent = None
    for t in torrents:
        if t.get("quality") == quality:
            selected_torrent = t
            break
    
    # Fall back to first available torrent
    if not selected_torrent:
        selected_torrent = torrents[0]
        print(f"Note: {quality} not available, using {selected_torrent.get('quality')}")
    
    print(f"\nTorrent: {selected_torrent.get('quality')} - {selected_torrent.get('size')}")
    print(f"  Seeds: {selected_torrent.get('seeds')} | Peers: {selected_torrent.get('peers')}")
    
    # Build magnet link
    torrent_hash = selected_torrent.get("hash")
    if not torrent_hash:
        print("Error: No torrent hash available")
        return False
    
    magnet = build_magnet(torrent_hash, movie["title"])
    
    # Connect to qBittorrent and add torrent
    print(f"\nAdding to qBittorrent...")
    print(f"  Save path: {save_path}")
    
    try:
        client = get_client()
        add_magnet(client, magnet, save_path=save_path)
        print("Successfully added torrent to qBittorrent!")
        return True
    except Exception as e:
        print(f"Error adding torrent: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Search YTS/YIFY and add movie torrent to qBittorrent"
    )
    parser.add_argument("query", help="Search query (movie title)")
    parser.add_argument("--save-path", "-o", required=True,
                        help="Path to save downloaded files")
    parser.add_argument("--index", "-i", type=int, default=0,
                        help="Index of search result to download (default: 0)")
    parser.add_argument("--quality", "-q", default="1080p",
                        choices=["720p", "1080p", "2160p", "3D"],
                        help="Preferred quality (default: 1080p)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List results without downloading")
    
    args = parser.parse_args()
    
    if args.list:
        # Just list results
        movies = search_movies(args.query)
        
        print(f"Found {len(movies)} movies:\n")
        for i, movie in enumerate(movies):
            print(f"[{i}] {movie['title']} ({movie['year']}) - IMDb: {movie.get('rating', 'N/A')}")
            torrents = movie.get("torrents", [])
            qualities = [t.get("quality") for t in torrents]
            print(f"    Available: {', '.join(qualities)}")
        return
    
    success = search_and_download(
        query=args.query,
        save_path=args.save_path,
        index=args.index,
        quality=args.quality
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

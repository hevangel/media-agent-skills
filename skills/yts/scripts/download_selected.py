"""
Download the movies selected in the YTS movie selector web app.

Reads the selection store written by movie_selector_server.py, then adds each
selected movie's torrent to qBittorrent and marks it as downloaded.

Usage:
    uv run python skills/yts/scripts/download_selected.py --list
    uv run python skills/yts/scripts/download_selected.py --dry-run
    uv run python skills/yts/scripts/download_selected.py --quality 1080p --save-path /path/to/downloads
    uv run python skills/yts/scripts/download_selected.py --status downloaded --list
"""

import argparse
import re
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "skills" / "qbittorrent" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import movie_selection_store as store
from download_movie import build_magnet
from qbittorrent_client import get_client, add_magnet

FALLBACK_ORDER = ["2160p", "1080p", "720p"]


def pick_torrent(movie: dict, preferred: str) -> tuple[dict | None, str | None]:
    """Choose the torrent: the movie's explicitly queued quality first (set by
    the web UI quality buttons), then the CLI preference, then best available.
    Returns (torrent, fallback) where fallback is set when the queued/preferred
    quality was unavailable."""
    torrents = movie.get("torrents") or []
    wanted = movie.get("quality") or preferred
    for torrent in torrents:
        if torrent.get("quality") == wanted:
            return torrent, None
    for quality in [preferred] + [q for q in FALLBACK_ORDER if q != preferred]:
        for torrent in torrents:
            if torrent.get("quality") == quality:
                return torrent, quality
    return (torrents[0], torrents[0].get("quality")) if torrents else (None, None)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add the web-app selected movies' torrents to qBittorrent"
    )
    parser.add_argument("--status", default="pending", choices=sorted(store.VALID_STATUSES),
                        help="Which selection status to process (default: pending)")
    parser.add_argument("--quality", "-q", default="1080p",
                        choices=["2160p", "1080p", "720p"],
                        help="Preferred quality (default: 1080p, falls back to best available)")
    parser.add_argument("--save-path", "-o", default=None,
                        help="Optional qBittorrent save path (default: qBittorrent's own)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="Only list the selection, do not download")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Print the magnet links without contacting qBittorrent")
    parser.add_argument("--no-mark", action="store_true",
                        help="Do not mark processed movies as downloaded")
    args = parser.parse_args()

    items = store.list_selections(args.status)
    print(f"[progress] Selection store: {store.state_path()}")
    print(f"[progress] {len(items)} selected movie(s) with status '{args.status}'")
    if args.list or not items:
        for item in items:
            qualities = ", ".join(t.get("quality", "?") for t in item.get("torrents", []))
            print(f"  - {item['title']} ({item.get('year')}) [{item.get('status')}] {qualities}")
        return

    client = None
    added = failed = 0
    for item in items:
        torrent, fallback = pick_torrent(item, args.quality)
        if not torrent or not torrent.get("hash"):
            print(f"[progress] SKIP {item['title']}: no torrent with a hash")
            failed += 1
            continue
        torrent_hash = torrent["hash"]
        if not re.fullmatch(r"[0-9a-fA-F]{40}", torrent_hash):
            print(f"[progress] SKIP {item['title']}: invalid torrent hash")
            failed += 1
            continue

        name = f"{item['title']} ({item.get('year')})" if item.get("year") else item["title"]
        magnet = build_magnet(torrent_hash, name)
        wanted = item.get("quality") or args.quality
        note = "" if (fallback is None or fallback == wanted) \
            else f" (fallback, {wanted} unavailable)"
        print(f"[progress] {name} -> {torrent.get('quality')} {torrent.get('size', '')}{note}")

        if args.dry_run:
            print(f"           {magnet}")
            added += 1
            continue

        if client is None:
            print("[progress] Connecting to qBittorrent ...")
            client = get_client()
        add_magnet(client, magnet, save_path=args.save_path)
        print("[progress]   added to qBittorrent")
        added += 1
        if not args.no_mark:
            store.set_status(item["id"], "downloaded")

    print(f"[progress] Done: {added} added, {failed} failed"
          + ("" if args.dry_run or args.no_mark else " (marked as downloaded)"))


if __name__ == "__main__":
    main()

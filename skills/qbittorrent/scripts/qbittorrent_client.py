"""
qBittorrent API Client Utilities

This module provides helper functions to interact with qBittorrent
via the qbittorrent-api Python package.
"""

import os
from dotenv import load_dotenv
import qbittorrentapi

load_dotenv()


def get_client(
    host: str = os.getenv("QBITTORRENT_HOST", "http://localhost:8080"),
    username: str = os.getenv("QBITTORRENT_USERNAME", "admin"),
    password: str = os.getenv("QBITTORRENT_PASSWORD", "your_password")
) -> qbittorrentapi.Client:
    """
    Create and authenticate a qBittorrent client.
    
    Args:
        host: qBittorrent Web UI URL
        username: Login username
        password: Login password
    
    Returns:
        Authenticated qBittorrent client
    """
    client = qbittorrentapi.Client(
        host=host,
        username=username,
        password=password
    )
    client.auth_log_in()
    return client


def list_torrents(client: qbittorrentapi.Client) -> list[dict]:
    """
    List all torrents with their status information.
    
    Args:
        client: Authenticated qBittorrent client
    
    Returns:
        List of torrent info dictionaries
    """
    torrents = client.torrents_info()
    result = []
    
    for t in torrents:
        result.append({
            "name": t.name,
            "hash": t.hash,
            "state": t.state,
            "progress": t.progress * 100,
            "size_gb": t.size / (1024 ** 3),
            "dl_speed_mb": t.dlspeed / (1024 ** 2),
            "up_speed_mb": t.upspeed / (1024 ** 2),
            "save_path": t.save_path,
        })
    
    return result


def add_magnet(client: qbittorrentapi.Client, magnet_link: str, save_path: str = None) -> str:
    """
    Add a torrent via magnet link.
    
    Args:
        client: Authenticated qBittorrent client
        magnet_link: Magnet URI to add
        save_path: Optional download destination path
    
    Returns:
        Result status string
    """
    kwargs = {"urls": magnet_link}
    if save_path:
        kwargs["save_path"] = save_path
    
    return client.torrents_add(**kwargs)


def resume_torrent(client: qbittorrentapi.Client, torrent_hash: str) -> None:
    """
    Resume/start a torrent download.
    
    Args:
        client: Authenticated qBittorrent client
        torrent_hash: Hash of the torrent to resume
    """
    client.torrents_resume(torrent_hashes=torrent_hash)


def pause_torrent(client: qbittorrentapi.Client, torrent_hash: str) -> None:
    """
    Pause a torrent download.
    
    Args:
        client: Authenticated qBittorrent client
        torrent_hash: Hash of the torrent to pause
    """
    client.torrents_pause(torrent_hashes=torrent_hash)


def delete_torrent(
    client: qbittorrentapi.Client,
    torrent_hash: str,
    delete_files: bool = False
) -> None:
    """
    Delete a torrent from qBittorrent.
    
    Args:
        client: Authenticated qBittorrent client
        torrent_hash: Hash of the torrent to delete
        delete_files: If True, also delete downloaded files
    """
    client.torrents_delete(
        torrent_hashes=torrent_hash,
        delete_files=delete_files
    )


def get_torrent_by_hash(client: qbittorrentapi.Client, torrent_hash: str) -> dict | None:
    """
    Get a specific torrent by its hash.
    
    Args:
        client: Authenticated qBittorrent client
        torrent_hash: Hash of the torrent to find
    
    Returns:
        Torrent info dictionary or None if not found
    """
    torrents = client.torrents_info(torrent_hashes=torrent_hash)
    if torrents:
        t = torrents[0]
        return {
            "name": t.name,
            "hash": t.hash,
            "state": t.state,
            "progress": t.progress * 100,
            "size_gb": t.size / (1024 ** 3),
            "dl_speed_mb": t.dlspeed / (1024 ** 2),
            "up_speed_mb": t.upspeed / (1024 ** 2),
            "save_path": t.save_path,
        }
    return None


if __name__ == "__main__":
    # Example usage
    client = get_client()
    
    print("Current torrents:")
    print("-" * 60)
    
    for torrent in list_torrents(client):
        print(f"Name: {torrent['name']}")
        print(f"  State: {torrent['state']}")
        print(f"  Progress: {torrent['progress']:.1f}%")
        print(f"  Size: {torrent['size_gb']:.2f} GB")
        print()

"""
Get Jellyfin server system information and configuration.
Useful for verifying connectivity and checking server status.
"""

import json
from pathlib import Path

try:
    from client import get_jellyfin_client
except ImportError:
    from .client import get_jellyfin_client


def get_system_info():
    """
    Get the Jellyfin server system configuration.

    Returns:
        dict: Server system configuration including version, paths, etc.
    """
    client = get_jellyfin_client()

    print("Fetching server system info...")
    info = client.jellyfin.get_system_info()

    print(f"\nServer Name: {info.get('ServerName', 'N/A')}")
    print(f"Version: {info.get('UICulture', 'N/A')}")
    print(f"Log Path: {info.get('LogPath', 'N/A')}")
    print(f"Transcode Path: {info.get('TranscodingTempPath', 'N/A')}")

    return info


def get_public_info():
    """
    Get public server information (does not require authentication).

    Returns:
        dict: Public server info.
    """
    client = get_jellyfin_client()
    print("Fetching public server info...")
    info = client.jellyfin.try_server()
    print(f"\nServer Name: {info.get('ServerName', 'N/A')}")
    print(f"Version: {info.get('Version', 'N/A')}")
    print(f"Server ID: {info.get('Id', 'N/A')}")
    print(f"OS: {info.get('OperatingSystem', 'N/A')}")
    return info


if __name__ == "__main__":
    print("=== Public Server Info ===")
    pub = get_public_info()
    print()

    print("=== System Configuration ===")
    sys_info = get_system_info()

    # Save to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "jellyfin_system_info.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"public_info": pub, "system_info": sys_info}, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {output_path}")

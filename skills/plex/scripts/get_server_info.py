"""
Get Plex server system information and configuration.
Useful for verifying connectivity and checking server status.
"""

import json
from pathlib import Path

try:
    from client import get_plex_client
except ImportError:
    from .client import get_plex_client


def get_server_info():
    """
    Get detailed Plex server information.

    Returns:
        dict: Server info including name, version, platform, transcoder settings.
    """
    plex = get_plex_client()
    print("Fetching server info...")

    info = {
        "friendlyName": plex.friendlyName,
        "version": plex.version,
        "platform": plex.platform,
        "platformVersion": plex.platformVersion,
        "machineIdentifier": plex.machineIdentifier,
        "myPlexUsername": plex.myPlexUsername,
        "transcoderActiveVideoSessions": plex.transcoderActiveVideoSessions,
        "updatedAt": str(plex.updatedAt) if hasattr(plex, "updatedAt") else "N/A",
    }

    print(f"\n{'='*80}")
    print(f"  Server Name: {info['friendlyName']}")
    print(f"  Version: {info['version']}")
    print(f"  Platform: {info['platform']} {info['platformVersion']}")
    print(f"  Machine ID: {info['machineIdentifier']}")
    print(f"  Username: {info['myPlexUsername']}")
    print(f"  Active Transcode Sessions: {info['transcoderActiveVideoSessions']}")
    print(f"{'='*80}")

    return info


def get_server_accounts():
    """
    Get list of users/accounts on the server.

    Returns:
        list: A list of user dicts.
    """
    plex = get_plex_client()
    print("Fetching server accounts...")

    try:
        account = plex.myPlexAccount()
        users = account.users()
        results = [
            {
                "username": user.username,
                "email": getattr(user, "email", None),
                "title": getattr(user, "title", user.username),
            }
            for user in users
        ]
        # Add owner
        results.insert(0, {
            "username": account.username,
            "email": account.email,
            "title": account.title,
            "isOwner": True,
        })
        print(f"Found {len(results)} users.")
        return results
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return []


def get_active_sessions():
    """
    Get currently active playback sessions.

    Returns:
        list: A list of active session dicts.
    """
    plex = get_plex_client()
    print("Fetching active sessions...")

    sessions = plex.sessions()
    results = []
    for session in sessions:
        entry = {
            "title": session.title,
            "type": session.type,
            "user": getattr(session, "usernames", ["Unknown"])[0] if hasattr(session, "usernames") else "Unknown",
            "player": getattr(session.player, "title", "Unknown") if hasattr(session, "player") else "Unknown",
            "state": getattr(session.player, "state", "Unknown") if hasattr(session, "player") else "Unknown",
        }
        results.append(entry)

    print(f"Found {len(results)} active sessions.")
    return results


if __name__ == "__main__":
    print("=== Server Info ===")
    server_info = get_server_info()

    print("\n=== Active Sessions ===")
    sessions = get_active_sessions()
    for s in sessions:
        print(f"  {s['user']} playing '{s['title']}' on {s['player']} ({s['state']})")
    if not sessions:
        print("  No active sessions.")

    # Save to temp
    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "plex_server_info.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"server": server_info, "sessions": sessions}, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nServer info saved to {output_path}")

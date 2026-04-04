"""
Plex API client setup using python-plexapi.
Supports multiple authentication methods:

  1. Direct token auth (PLEX_URL + PLEX_TOKEN)
  2. MyPlex account discovery (PLEX_USERNAME + PLEX_PASSWORD)

If the token fails or is missing, falls back to MyPlex login which
automatically discovers and connects to the server.

Run get_token.py to obtain a valid token interactively.
"""

import os
from pathlib import Path
from plexapi.server import PlexServer

try:
    from config import PLEX_URL, PLEX_TOKEN, PLEX_USERNAME, PLEX_PASSWORD
except ImportError:
    from .config import PLEX_URL, PLEX_TOKEN, PLEX_USERNAME, PLEX_PASSWORD


def _connect_with_token(url, token):
    """Attempt direct token connection."""
    plex = PlexServer(url, token)
    return plex


def _connect_with_myplex(username, password, server_url=None):
    """Authenticate via MyPlex account and connect to the server."""
    from plexapi.myplex import MyPlexAccount

    print(f"Logging in to plex.tv as '{username}'...")
    account = MyPlexAccount(username, password)

    # Find the server matching PLEX_URL, or pick the first one
    resources = [r for r in account.resources() if r.provides == "server"]
    if not resources:
        raise ValueError("No Plex servers found on this account.")

    target = None
    if server_url:
        for r in resources:
            for conn in r.connections:
                if conn.uri.rstrip("/") == server_url.rstrip("/"):
                    target = r
                    break
            if target:
                break

    if not target:
        target = resources[0]
        print(f"Connecting to server '{target.name}'...")

    plex = target.connect()

    # Save the token to .env for future direct auth
    try:
        from dotenv import set_key
        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        if env_path.exists():
            set_key(str(env_path), "PLEX_TOKEN", plex._token)
            if plex._baseurl:
                set_key(str(env_path), "PLEX_URL", plex._baseurl)
            print(f"Saved PLEX_TOKEN to .env for future use.")
    except Exception:
        pass  # non-critical

    return plex


def get_plex_client():
    """
    Create and authenticate a PlexServer instance.

    Tries token auth first, then falls back to MyPlex login.

    Returns:
        PlexServer: An authenticated Plex server instance.
    """
    # Method 1: Direct token
    if PLEX_URL and PLEX_TOKEN:
        try:
            print(f"Connecting to Plex server at {PLEX_URL}...")
            plex = _connect_with_token(PLEX_URL, PLEX_TOKEN)
            print(f"Successfully connected to '{plex.friendlyName}' (v{plex.version}).")
            return plex
        except Exception as e:
            print(f"Token auth failed: {e}")
            print("Falling back to MyPlex login...")

    # Method 2: MyPlex account
    if PLEX_USERNAME and PLEX_PASSWORD:
        try:
            plex = _connect_with_myplex(PLEX_USERNAME, PLEX_PASSWORD, PLEX_URL)
            print(f"Successfully connected to '{plex.friendlyName}' (v{plex.version}).")
            return plex
        except Exception as e:
            print(f"MyPlex login failed: {e}")

    raise ValueError(
        "Could not connect to Plex. Set one of:\n"
        "  1. PLEX_URL + PLEX_TOKEN in .env (run get_token.py to obtain)\n"
        "  2. PLEX_USERNAME + PLEX_PASSWORD in .env for MyPlex login\n"
        "See SKILL.md for details."
    )


if __name__ == "__main__":
    server = get_plex_client()
    print(f"Server Name: {server.friendlyName}")
    print(f"Version: {server.version}")
    print(f"Platform: {server.platform}")
    print(f"Machine ID: {server.machineIdentifier}")
    print(f"My Plex Username: {server.myPlexUsername}")

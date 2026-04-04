"""
Helper script to obtain a valid Plex auth token.

Supports multiple methods:
  1. MyPlex account login (email/username + password)
  2. Interactive browser-based PIN auth (no password needed)
  3. Manual token entry

The token is saved to the .env file automatically.

Usage:
    cd skills/plex/code_snippet
    uv run python get_token.py
"""

import os
import sys
import time
from pathlib import Path

# Ensure dotenv is available
from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_PATH)


def method_myplex_login():
    """Authenticate via MyPlex username/email and password."""
    from plexapi.myplex import MyPlexAccount

    print("\n--- MyPlex Account Login ---")
    username = input("Plex username or email: ").strip()
    password = input("Plex password: ").strip()

    if not username or not password:
        print("Error: Username and password are required.")
        return None, None

    try:
        print("Logging in to plex.tv...")
        account = MyPlexAccount(username, password)
        token = account.authenticationToken
        print(f"Login successful! Account: {account.username}")

        # List available servers
        resources = [r for r in account.resources() if r.provides == "server"]
        if resources:
            print(f"\nAvailable Plex servers:")
            for i, r in enumerate(resources, 1):
                print(f"  [{i}] {r.name}")
            if len(resources) == 1:
                server = resources[0]
            else:
                choice = input(f"Select server [1-{len(resources)}]: ").strip()
                server = resources[int(choice) - 1]
            print(f"Selected server: {server.name}")
            # Connect to get the server-specific token
            plex = server.connect()
            server_token = plex._token
            server_url = plex._baseurl
            print(f"Server URL: {server_url}")
            print(f"Server Token: {server_token[:8]}...")
            return server_url, server_token
        else:
            print("No Plex servers found on this account.")
            print(f"Using account token: {token[:8]}...")
            return None, token

    except Exception as e:
        print(f"Error: {e}")
        return None, None


def method_pin_auth():
    """Authenticate via Plex PIN (browser-based, no password needed)."""
    from plexapi.myplex import MyPlexPinLogin

    print("\n--- Browser-based PIN Auth ---")
    print("This will open a URL in your browser to authenticate.")

    pin_login = MyPlexPinLogin()
    print(f"\nPlease open this URL in your browser and sign in:")
    print(f"  {pin_login.oauthUrl()}")
    print(f"\nWaiting for authentication (timeout: 120s)...")

    if pin_login.run(timeout=120):
        token = pin_login.token
        print(f"\nAuthentication successful!")
        print(f"Token: {token[:8]}...")

        # Try to find the server
        from plexapi.myplex import MyPlexAccount
        try:
            account = MyPlexAccount(token=token)
            resources = [r for r in account.resources() if r.provides == "server"]
            if resources:
                print(f"\nAvailable Plex servers:")
                for i, r in enumerate(resources, 1):
                    print(f"  [{i}] {r.name}")
                if len(resources) == 1:
                    server = resources[0]
                else:
                    choice = input(f"Select server [1-{len(resources)}]: ").strip()
                    server = resources[int(choice) - 1]
                plex = server.connect()
                return plex._baseurl, plex._token
        except Exception as e:
            print(f"Warning: Could not list servers: {e}")

        return None, token
    else:
        print("Authentication timed out or was cancelled.")
        return None, None


def method_manual_token():
    """Manually enter an existing Plex token."""
    print("\n--- Manual Token Entry ---")
    print("To find your token:")
    print("  1. Open Plex Web App (app.plex.tv)")
    print("  2. Browse to any media item")
    print("  3. Click '...' menu > 'Get Info' > 'View XML'")
    print("  4. Copy the X-Plex-Token value from the URL")
    print()
    token = input("Paste your X-Plex-Token: ").strip()
    if not token:
        print("Error: Token is required.")
        return None, None

    default_url = os.getenv("PLEX_URL", "http://localhost:32400")
    url = input(f"Plex server URL [{default_url}]: ").strip()
    if not url:
        url = default_url

    return url, token


def verify_token(url, token):
    """Verify the token works by connecting to the server."""
    from plexapi.server import PlexServer

    print(f"\nVerifying token against {url}...")
    try:
        plex = PlexServer(url, token)
        print(f"  Server: {plex.friendlyName}")
        print(f"  Version: {plex.version}")
        print(f"  Libraries: {len(plex.library.sections())}")
        return True
    except Exception as e:
        print(f"  Verification failed: {e}")
        return False


def save_to_env(url, token):
    """Save the token and URL to the .env file."""
    if not ENV_PATH.exists():
        print(f"Warning: .env file not found at {ENV_PATH}")
        return False

    print(f"\nSaving credentials to {ENV_PATH}...")
    set_key(str(ENV_PATH), "PLEX_URL", url)
    set_key(str(ENV_PATH), "PLEX_TOKEN", token)
    print("  PLEX_URL and PLEX_TOKEN saved successfully.")
    return True


def main():
    print("=" * 60)
    print("  Plex Token Helper")
    print("=" * 60)
    print("\nChoose authentication method:")
    print("  [1] MyPlex login (username/email + password)")
    print("  [2] Browser-based PIN auth (no password needed)")
    print("  [3] Manual token entry (paste existing token)")
    print()

    choice = input("Select method [1/2/3]: ").strip()

    if choice == "1":
        url, token = method_myplex_login()
    elif choice == "2":
        url, token = method_pin_auth()
    elif choice == "3":
        url, token = method_manual_token()
    else:
        print("Invalid choice.")
        sys.exit(1)

    if not token:
        print("\nFailed to obtain token. Please try again.")
        sys.exit(1)

    # Use existing URL if not returned
    if not url:
        url = os.getenv("PLEX_URL", "http://localhost:32400")
        custom_url = input(f"Plex server URL [{url}]: ").strip()
        if custom_url:
            url = custom_url

    # Verify
    if verify_token(url, token):
        save_to_env(url, token)
        print("\nDone! You can now use the Plex skill scripts.")
    else:
        save_anyway = input("\nToken verification failed. Save anyway? [y/N]: ").strip().lower()
        if save_anyway == "y":
            save_to_env(url, token)
        else:
            print("Token not saved.")
            sys.exit(1)


if __name__ == "__main__":
    main()

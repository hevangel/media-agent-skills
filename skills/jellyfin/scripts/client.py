"""
Jellyfin API client setup using jellyfin-apiclient-python.
Authenticates via API key from .env configuration.

When using an API key (not username/password), the library does not
automatically resolve {UserId}. This module works around that by
fetching the user list after authentication and setting auth.user_id
so user-scoped endpoints work correctly.
"""

from jellyfin_apiclient_python import JellyfinClient

try:
    from config import SERVER_URL, API_KEY
except ImportError:
    from .config import SERVER_URL, API_KEY


def get_jellyfin_client():
    """
    Create and authenticate a JellyfinClient using an API key.

    Returns:
        JellyfinClient: An authenticated Jellyfin client instance.
    """
    client = JellyfinClient()
    client.config.data["app.name"] = "ai_agents"
    client.config.data["app.version"] = "0.1.0"
    # Required for API key auth - prevents KeyError in connection_manager
    client.config.data["auth.ssl"] = False

    print(f"Connecting to Jellyfin server at {SERVER_URL}...")
    client.authenticate(
        {"Servers": [{"AccessToken": API_KEY, "address": SERVER_URL}]},
        discover=False,
    )

    # For API key auth, manually set auth.server and auth.token so
    # {UserId} placeholder replacement and HTTP requests work properly
    client.config.data["auth.server"] = SERVER_URL
    client.config.data["auth.token"] = API_KEY

    # Resolve UserId by fetching the user list (API key has admin access)
    users = client.jellyfin.get_users()
    if users:
        # Use the first admin user, or fall back to the first user
        admin_user = next(
            (u for u in users if u.get("Policy", {}).get("IsAdministrator")),
            users[0],
        )
        user_id = admin_user["Id"]
        client.config.data["auth.user_id"] = user_id
        print(f"Successfully authenticated as '{admin_user['Name']}' (ID: {user_id}).")
    else:
        print("Warning: No users found on server. User-scoped API calls may fail.")

    return client


if __name__ == "__main__":
    jf_client = get_jellyfin_client()
    print(f"Auth server: {jf_client.config.data.get('auth.server')}")
    print(f"Auth user_id: {jf_client.config.data.get('auth.user_id')}")

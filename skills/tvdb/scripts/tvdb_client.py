"""
TVDB API client wrapper.
Provides a configured tvdb_v4_official.TVDB instance using TVDB_API_KEY from .env.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

import tvdb_v4_official


def get_client() -> tvdb_v4_official.TVDB:
    """Create and return an authenticated TVDB client."""
    api_key = os.environ.get("TVDB_API_KEY")
    if not api_key:
        print("Error: TVDB_API_KEY not set in environment or .env file.")
        sys.exit(1)
    print("Authenticating with TVDB API...")
    client = tvdb_v4_official.TVDB(api_key)
    print("Authenticated successfully.")
    return client

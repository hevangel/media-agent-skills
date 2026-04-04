"""
Configuration for Plex API
Loads environment variables from .env file.

Supports two authentication modes:
  1. Direct token auth: PLEX_URL + PLEX_TOKEN
  2. MyPlex account auth: PLEX_URL + PLEX_USERNAME + PLEX_PASSWORD

Run get_token.py to obtain a valid token interactively.
"""
import os
from dotenv import load_dotenv

load_dotenv()

PLEX_URL = os.getenv("PLEX_URL", "http://localhost:32400")
PLEX_TOKEN = os.getenv("PLEX_TOKEN", "")
PLEX_USERNAME = os.getenv("PLEX_USERNAME", "")
PLEX_PASSWORD = os.getenv("PLEX_PASSWORD", "")

"""
Configuration for Jellyfin API
Loads environment variables from .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv("JELLYFIN_HOST", "http://localhost:8096")
API_KEY = os.getenv("JELLYFIN_API_KEY", "")

"""
Configuration for Kavita API
Loads environment variables from .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv("KAVITA_HOST", "http://localhost/kavita")
API_KEY = os.getenv("KAVITA_API_KEY", "your_api_key")
USERNAME = os.getenv("KAVITA_USERNAME", "your_username")
PASSWORD = os.getenv("KAVITA_PASSWORD", "your_password")

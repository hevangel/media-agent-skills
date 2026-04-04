"""
Audiobookbay HTTP client with configuration.
"""

import time
import random
import urllib3
import requests
import os
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context
from dotenv import load_dotenv
from typing import Optional

# Suppress SSL warnings when verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

class LegacySSLAdapter(HTTPAdapter):
    """
    A custom HTTP Adapter that allows legacy SSL/TLS versions and ciphers.
    Useful for connecting to servers with outdated SSL configurations.
    """
    def init_poolmanager(self, connections, maxsize, block=False):
        # Create a context that is permissive
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Allow legacy renegotiation if supported (OpenSSL 3.0+)
        if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
            ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
            
        # You can set minimum version here if needed, e.g. ssl.TLSVersion.TLSv1
        
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

class AudiobookbayClient:
    """HTTP client for Audiobookbay with rate limiting and configuration."""

    # Default trackers for magnet links
    DEFAULT_TRACKERS = [
        "udp://tracker.openbittorrent.com:80",
        "udp://opentor.org:2710",
        "udp://tracker.ccc.de:80",
        "udp://tracker.blackunicorn.xyz:6969",
        "udp://tracker.coppersurfer.tk:6969",
        "udp://tracker.leechers-paradise.org:6969",
    ]

    def __init__(
        self,
        hostname: str = None,
        verify_ssl: bool = False,
        timeout: int = 15,
        rate_limit_delay: float = 2.0,
        rate_limit_jitter: float = 1.0,
    ):
        """
        Initialize the Audiobookbay client.

        Args:
            hostname: The Audiobookbay hostname to use.
                      Options: audiobookbay.lu, audiobookbay.is, audiobookbay.nl
            verify_ssl: Whether to verify SSL certificates.
            timeout: Request timeout in seconds.
            rate_limit_delay: Base delay between requests in seconds.
            rate_limit_jitter: Random jitter to add to delay.
        """
        if hostname is None:
            # Try to get from env, else default
            hostname = os.getenv("AUDIOBOOKBAY_URL", "audiobookbay.lu").replace("https://", "").replace("http://", "").strip("/")
            
        self.hostname = hostname
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.rate_limit_jitter = rate_limit_jitter
        
        if hostname.startswith("http"):
             self.base_url = hostname.rstrip("/")
        else:
             self.base_url = f"https://{hostname}"
        
        self.username = os.getenv("AUDIOBOOKBAY_USERNAME", "your_username")
        self.password = os.getenv("AUDIOBOOKBAY_PASSWORD", "your_password")

        self.session = requests.Session()
        
        # Mount the custom LegacySSLAdapter for HTTPS
        adapter = LegacySSLAdapter()
        self.session.mount("https://", adapter)
        
        self.session.headers.update(self._get_headers())

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

    def get(self, url: str) -> Optional[requests.Response]:
        """
        Make a GET request with error handling.

        Args:
            url: URL to fetch.

        Returns:
            Response object or None on failure.
        """
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return None

    def wait(self):
        """Wait with rate limiting delay and jitter."""
        delay = self.rate_limit_delay + random.uniform(0, self.rate_limit_jitter)
        time.sleep(delay)

    def build_search_url(self, query: str, page: int = 1) -> str:
        """
        Build a simple search URL.

        Args:
            query: Search query.
            page: Page number.

        Returns:
            Full search URL.
        """
        encoded_query = query.lower().replace(" ", "+")
        return f"{self.base_url}/page/{page}/?s={encoded_query}"

    def build_advanced_search_url(
        self,
        query: str,
        params: dict,
        page: int = 1
    ) -> str:
        """
        Build an advanced search URL with category filters.

        Args:
            query: Search query.
            params: Dictionary of advanced search parameters.
            page: Page number.

        Returns:
            Full advanced search URL.
        """
        from urllib.parse import urlencode

        encoded_query = query.lower().replace(" ", "+")
        base = f"{self.base_url}/page/{page}/?s={encoded_query}"

        # Build query string for array parameters
        query_parts = []
        for key, value in params.items():
            if isinstance(value, list):
                for item in value:
                    query_parts.append(f"{key}={item}")
            else:
                query_parts.append(f"{key}={value}")

        if query_parts:
            return f"{base}&{'&'.join(query_parts)}"
        return base

    def normalize_link(self, link: str) -> str:
        """
        Normalize a link to be absolute.

        Args:
            link: Relative or absolute link.

        Returns:
            Absolute URL.
        """
        if link.startswith("http"):
            return link
        return f"{self.base_url}{link}"


# Default client instance
_default_client: Optional[AudiobookbayClient] = None


def get_client() -> AudiobookbayClient:
    """Get or create the default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = AudiobookbayClient()
    return _default_client


def set_client(client: AudiobookbayClient):
    """Set the default client instance."""
    global _default_client
    _default_client = client

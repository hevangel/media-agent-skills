"""
Audible Cover Scraper using Web Search and Direct URL Scraping
Searches for audiobook covers and downloads them.
"""

import re
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class AudibleSearchResult:
    """Result from an Audible search."""
    success: bool
    product_url: Optional[str] = None
    cover_url: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


class AudibleCoverScraper:
    """Scrapes cover images from Audible using web search."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def search_audible_url(self, author: str, title: str) -> Optional[str]:
        """
        Search for Audible URL using DuckDuckGo.

        Args:
            author: Author name
            title: Book title

        Returns:
            Audible URL if found
        """
        try:
            # Use DuckDuckGo MCP to search
            author_clean = re.sub(r'[^\w\s]', '', author).strip()
            title_clean = re.sub(r'[^\w\s]', '', title).strip()
            title_clean = re.sub(r'^\d+\s+', '', title_clean)

            search_query = f'"{author_clean}" "{title_clean}" audiobook site:audible.com'
            print(f"  Searching: {search_query}")

            # Try to use DuckDuckGo MCP search
            results = mcp_duckduckgo_search(query=search_query, max_results=5)

            # Parse the result which may be a dict with 'result' key containing formatted text
            if isinstance(results, dict) and 'result' in results:
                result_text = results['result']
                # Extract URLs from the text
                urls = re.findall(r'URL:\s*(https://www\.audible\.com/pd/[^\s\n]+)', result_text)
                if urls:
                    print(f"  ✓ Found Audible URL")
                    return urls[0]
            elif isinstance(results, list):
                for result in results:
                    url = result.get('url', '')
                    if 'audible.com' in url and '/pd/' in url:
                        print(f"  ✓ Found Audible URL")
                        return url

            return None

        except NameError:
            print(f"  ⚠ DuckDuckGo MCP not available, trying direct search")
            # Fallback: construct likely Audible URL
            return None
        except Exception as e:
            print(f"  ⚠ Search error: {str(e)[:100]}")
            return None

    def extract_cover_from_audible_page(self, audible_url: str) -> Optional[str]:
        """
        Extract cover image URL from Audible product page.

        Args:
            audible_url: Audible product page URL

        Returns:
            Cover image URL if found
        """
        try:
            print(f"  Fetching Audible page...")
            response = self.session.get(audible_url, timeout=15)
            response.raise_for_status()
            html = response.text

            # Try multiple patterns to find cover images
            patterns = [
                # High-resolution patterns
                r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9+]+)\._SL500_\.jpg',
                r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9+]+)\.jpg',
                # JSON-LD structured data
                r'"image"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
                # Open Graph meta tag
                r'<meta property="og:image" content="(https://m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
                # Product image
                r'<img[^>]*class="[^"]*product[^"]*"[^>]*src="(https://m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    if pattern.startswith(r'https://'):
                        # Pattern captured full URL
                        url = matches[0]
                        # Ensure high resolution
                        if '._SL' not in url:
                            url = re.sub(r'\.jpg$', '._SL500_.jpg', url)
                        print(f"  ✓ Found cover URL")
                        return url
                    else:
                        # Pattern captured just ID
                        image_id = matches[0]
                        url = f"https://m.media-amazon.com/images/I/{image_id}._SL500_.jpg"
                        print(f"  ✓ Found cover URL")
                        return url

            # Fallback: look for any media-amazon image
            all_images = re.findall(r'https://m\.media-amazon\.com/images/I/[A-Za-z0-9+]+\.jpg', html)
            if all_images:
                # Get the first high-quality one
                for img in all_images:
                    if len(img) > 60:  # Likely a product image
                        url = re.sub(r'\.jpg$', '._SL500_.jpg', img)
                        print(f"  ✓ Found cover URL (fallback)")
                        return url

            return None

        except Exception as e:
            print(f"  ✗ Error extracting cover: {str(e)[:100]}")
            return None

    def search_and_get_cover(self, author: str, title: str) -> AudibleSearchResult:
        """
        Search for an audiobook on Audible and get the cover URL.

        Args:
            author: Author name
            title: Book title

        Returns:
            AudibleSearchResult with cover URL if found
        """
        try:
            # Search for Audible URL
            audible_url = self.search_audible_url(author, title)

            if not audible_url:
                return AudibleSearchResult(
                    success=False,
                    error="Could not find Audible product page"
                )

            # Extract cover from page
            cover_url = self.extract_cover_from_audible_page(audible_url)

            if cover_url:
                return AudibleSearchResult(
                    success=True,
                    product_url=audible_url,
                    cover_url=cover_url,
                    title=title
                )
            else:
                return AudibleSearchResult(
                    success=False,
                    product_url=audible_url,
                    error="Could not extract cover image from page"
                )

        except Exception as e:
            return AudibleSearchResult(
                success=False,
                error=str(e)[:200]
            )

    def close(self):
        """Clean up resources."""
        self.session.close()


def search_audible_with_browser(author: str, title: str) -> Optional[str]:
    """
    Convenience function to search Audible and return cover URL.

    Args:
        author: Author name
        title: Book title

    Returns:
        Cover URL if found, None otherwise
    """
    scraper = AudibleCoverScraper()
    result = scraper.search_and_get_cover(author, title)

    if result.success:
        return result.cover_url
    else:
        print(f"  ✗ Search failed: {result.error}")
        return None

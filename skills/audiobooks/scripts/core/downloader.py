"""
Cover Downloader
Downloads cover images from various sources.
"""

import re
import requests
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class DownloadResult:
    """Result of a cover download operation."""
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    size_kb: Optional[float] = None


class CoverDownloader:
    """Downloads cover images from various sources."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def download_from_url(self, url: str, save_path: str) -> DownloadResult:
        """
        Download cover image from a direct URL.

        Args:
            url: Direct URL to the image
            save_path: Path where the image should be saved

        Returns:
            DownloadResult with success status and details
        """
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()

            # Verify it's an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type.lower():
                return DownloadResult(
                    success=False,
                    error=f"Not an image: {content_type}"
                )

            # Save the image
            with open(save_path, 'wb') as f:
                f.write(response.content)

            size_kb = len(response.content) / 1024

            return DownloadResult(
                success=True,
                file_path=save_path,
                size_kb=size_kb
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=str(e)[:100]
            )

    def extract_audible_cover_url(self, audible_page_url: str) -> Optional[str]:
        """
        Extract cover image URL from an Audible product page.

        Args:
            audible_page_url: URL to the Audible product page

        Returns:
            URL to the cover image, or None if not found
        """
        try:
            response = self.session.get(audible_page_url, timeout=15)
            response.raise_for_status()
            html = response.text

            # Try multiple patterns to find cover images
            patterns = [
                # Audible specific patterns
                r'"image":"(https://[^"]*m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
                r'<img[^>]*src="(https://[^"]*m\.media-amazon\.com/images/I/[^"]+\.jpg)"[^>]*product',
                r'<img[^>]*class="[^"]*bc-pub-block[^"]*"[^>]*src="(https://[^"]+\.jpg)"',
                r'<meta property="og:image" content="(https://[^"]*m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
                # Amazon specific patterns
                r'data-a-dynamic-image="\{&quot;(https://m\.media-amazon\.com/images/I/[^&]+\.jpg)',
                r'"largeImage":"(https://[^"]*\.jpg)"',
                r'<img[^>]*id="landingImage"[^>]*src="(https://[^"]+\.jpg)"',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    url = matches[0]
                    # Ensure high resolution
                    url = re.sub(r'\._[A-Z0-9_,]+_\.', '._SL500_.', url)
                    # Remove any URL encoding
                    url = url.replace('&quot;', '').split('"')[0]
                    return url

            # Fallback: look for any media-amazon image
            all_images = re.findall(r'https://m\.media-amazon\.com/images/I/[A-Za-z0-9+]+\.jpg', html)
            if all_images:
                # Return the first one with decent size indicator
                for img in all_images:
                    if 'SL' in img or len(img) > 50:  # Likely a cover
                        return re.sub(r'\._[A-Z0-9_,]+_\.', '._SL500_.', img)
                return all_images[0]

            return None

        except Exception as e:
            print(f"  Error extracting cover: {str(e)[:100]}")
            return None

    def download_from_audible_page(self, audible_page_url: str, save_path: str) -> DownloadResult:
        """
        Download cover image from an Audible product page.

        Args:
            audible_page_url: URL to the Audible product page
            save_path: Path where the image should be saved

        Returns:
            DownloadResult with success status and details
        """
        # Extract cover URL from page
        cover_url = self.extract_audible_cover_url(audible_page_url)

        if not cover_url:
            return DownloadResult(
                success=False,
                error="Could not extract cover URL from page"
            )

        print(f"  Found cover URL: {cover_url[:80]}...")

        # Download the cover
        return self.download_from_url(cover_url, save_path)

    def search_audible(self, author: str, title: str) -> Optional[str]:
        """
        Search for an audiobook on Audible and return the product page URL.

        Note: This is a placeholder for future implementation.
        Currently returns None - actual search would require web scraping or API access.

        Args:
            author: Author name
            title: Book title

        Returns:
            URL to the Audible product page, or None if not found
        """
        # Clean up search terms
        author_clean = re.sub(r'[^\w\s]', '', author).strip()
        title_clean = re.sub(r'[^\w\s]', '', title).strip()
        title_clean = re.sub(r'^\d+\s+', '', title_clean)  # Remove leading numbers

        search_query = f'"{author_clean}" "{title_clean}" audiobook site:audible.com'
        print(f"  Search query: {search_query}")
        print(f"  Note: Automated search not implemented. Please search manually.")

        # TODO: Implement actual search using DuckDuckGo MCP or similar
        return None

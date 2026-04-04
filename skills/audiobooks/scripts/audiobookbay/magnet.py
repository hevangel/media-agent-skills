"""
Audiobookbay magnet link extraction.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

from .client import AudiobookbayClient, get_client
from .models import AudiobookResult


def extract_magnet_link(
    details_url: str,
    client: Optional[AudiobookbayClient] = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Extract info hash and generate magnet link from audiobook details page.

    Args:
        details_url: URL of the audiobook details page.
        client: Optional client instance (uses default if not provided).

    Returns:
        Tuple of (info_hash, magnet_link) or (None, None) on failure.
    """
    if client is None:
        client = get_client()

    print(f"Fetching details page: {details_url}")
    response = client.get(details_url)

    if response is None:
        return None, None

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract Info Hash
        info_hash_row = soup.find("td", string=re.compile(r"Info Hash", re.IGNORECASE))
        if not info_hash_row:
            print("[ERROR] Info Hash not found on the page.")
            return None, None

        info_hash = info_hash_row.find_next_sibling("td").text.strip()

        # Extract Trackers
        tracker_rows = soup.find_all("td", string=re.compile(r"udp://|http://", re.IGNORECASE))
        trackers = [row.text.strip() for row in tracker_rows]

        if not trackers:
            print("[WARNING] No trackers found. Using default trackers.")
            trackers = client.DEFAULT_TRACKERS

        # Construct the magnet link
        trackers_query = "&".join(
            f"tr={requests.utils.quote(tracker)}" for tracker in trackers
        )
        magnet_link = f"magnet:?xt=urn:btih:{info_hash}&{trackers_query}"

        return info_hash, magnet_link

    except Exception as e:
        print(f"[ERROR] Failed to extract magnet link: {e}")
        return None, None


def enrich_with_magnets(
    results: list[AudiobookResult],
    client: Optional[AudiobookbayClient] = None
) -> list[AudiobookResult]:
    """
    Enrich search results with magnet links.

    Args:
        results: List of AudiobookResult objects.
        client: Optional client instance (uses default if not provided).

    Returns:
        The same list with info_hash and magnet_link populated.
    """
    if client is None:
        client = get_client()

    print(f"\nExtracting magnet links for {len(results)} results...")

    for i, result in enumerate(results):
        print(f"\n[{i+1}/{len(results)}] {result.title}")
        info_hash, magnet = extract_magnet_link(result.link, client)
        result.info_hash = info_hash
        result.magnet_link = magnet

        # Rate limiting between requests
        if i < len(results) - 1:
            client.wait()

    return results

"""
Audiobookbay search functionality with advanced search support.
"""

import re
from enum import Enum
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional

from .client import AudiobookbayClient, get_client
from .models import AudiobookResult


class SearchIn(Enum):
    """Search target options."""
    TITLE_AUTHOR = "1"
    CONTENT = "2"
    TORRENT = "3"


class Category(Enum):
    """Audiobookbay categories with their IDs."""
    POST_APOCALYPTIC = "36021"
    ACTION = "101"
    ADULTS = "23195"
    ADVENTURE = "232"
    ANTHOLOGY = "151"
    ART = "30"
    AUTOBIOGRAPHY_BIOGRAPHIES = "24289"
    BESTSELLERS = "16650"
    BUSINESS = "104"
    CHILDREN = "98"
    CLASSIC = "85"
    COMPUTER = "233"
    CONTEMPORARY = "231"
    CRIME = "121"
    DETECTIVE = "122"
    DOCTOR_WHO = "15243"
    DOCUMENTARY = "107"
    EDUCATION = "105"
    FANTASY = "65"
    FULL_CAST = "17502"
    GAY = "17180"
    GENERAL_FICTION = "21110"
    HISTORICAL_FICTION = "2315"
    HISTORY = "19"
    HORROR = "2551"
    HUMOR = "234"
    LECTURE = "115"
    LESBIAN = "20962"
    LGBT = "20404"
    LIBERTARIAN = "23198"
    LIGHT_NOVEL = "20738"
    LITERATURE = "76"
    LITRPG = "30126"
    MILITARY = "790"
    MISC_NONFICTION = "25881"
    MYSTERY = "111"
    NOVEL = "108"
    OTHER = "1"
    PARANORMAL = "235"
    PLAYS_THEATER = "26398"
    POETRY = "1699"
    POLITICAL = "2010"
    RADIO_PRODUCTIONS = "26397"
    ROMANCE = "103"
    SCI_FI = "100"
    SCIENCE = "99"
    SELF_HELP = "1663"
    SEX_SCENES = "23197"
    SHORT_STORY = "16706"
    SPIRITUAL_RELIGIOUS = "22"
    SPORT_RECREATION = "432"
    SUSPENSE = "156"
    TEEN_YOUNG_ADULT = "2986"
    THRILLER = "102"
    TRUE_CRIME = "11685"
    TUTORIAL = "110"
    VIOLENCE = "6322"
    WESTERNS = "26010"
    ZOMBIES = "23196"


@dataclass
class AdvancedSearchOptions:
    """Options for advanced search."""
    # Search targets (where to search)
    search_in_title_author: bool = True
    search_in_content: bool = True
    search_in_torrent: bool = True

    # Exact match
    exact_match: bool = False

    # Categories to include (empty = all)
    include_categories: list[Category] = field(default_factory=list)

    # Categories to exclude
    exclude_categories: list[Category] = field(default_factory=list)

    def to_query_params(self) -> dict:
        """Convert options to URL query parameters."""
        params = {}

        # Search targets
        tt = []
        if self.search_in_title_author:
            tt.append(SearchIn.TITLE_AUTHOR.value)
        if self.search_in_content:
            tt.append(SearchIn.CONTENT.value)
        if self.search_in_torrent:
            tt.append(SearchIn.TORRENT.value)
        if tt:
            params["tt[]"] = tt

        # Exact match
        if self.exact_match:
            params["exact_match"] = "on"

        # Include categories
        if self.include_categories:
            params["include_cat[]"] = [cat.value for cat in self.include_categories]

        # Exclude categories
        if self.exclude_categories:
            params["exclude_cat[]"] = [f"-{cat.value}" for cat in self.exclude_categories]

        return params


def parse_post(post, client: AudiobookbayClient) -> Optional[AudiobookResult]:
    """
    Parse a single post element into an AudiobookResult.

    Args:
        post: BeautifulSoup element for the post.
        client: Audiobookbay client for URL normalization.

    Returns:
        AudiobookResult or None if parsing fails.
    """
    try:
        title_element = post.select_one(".postTitle > h2 > a")
        if not title_element:
            return None

        title = title_element.text.strip()
        link = client.normalize_link(title_element["href"])

        # Get cover image
        cover_img = post.select_one("img")
        cover = cover_img["src"] if cover_img and cover_img.get("src") else None

        # Get post info
        post_info = post.select_one(".postInfo")
        post_info_text = post_info.get_text(separator=" ", strip=True) if post_info else ""

        # Extract language
        language_match = re.search(
            r"Language:\s*(.*?)(?:\s*Keywords:|$)", post_info_text, re.DOTALL
        )
        language = language_match.group(1).strip() if language_match else "N/A"

        # Get details from postContent
        details_paragraph = post.select_one(".postContent p[style*='text-align:center']")
        post_date, book_format, bitrate, file_size = "N/A", "N/A", "N/A", "N/A"

        if details_paragraph:
            details_html = str(details_paragraph)

            post_date_match = re.search(r"Posted:\s*([^<]+)", details_html)
            post_date = post_date_match.group(1).strip() if post_date_match else "N/A"

            format_match = re.search(r"Format:\s*<span[^>]*>([^<]+)</span>", details_html)
            book_format = format_match.group(1).strip() if format_match else "N/A"

            bitrate_match = re.search(r"Bitrate:\s*<span[^>]*>([^<]+)</span>", details_html)
            bitrate = bitrate_match.group(1).strip() if bitrate_match else "N/A"

            file_size_match = re.search(
                r"File Size:\s*<span[^>]*>([^<]+)</span>\s*([^<]+)", details_html
            )
            if file_size_match:
                file_size = f"{file_size_match.group(1).strip()} {file_size_match.group(2).strip()}"

        return AudiobookResult(
            title=title,
            link=link,
            cover=cover,
            language=language,
            post_date=post_date,
            format=book_format,
            bitrate=bitrate,
            file_size=file_size,
        )

    except Exception as e:
        print(f"[ERROR] Could not process post: {e}")
        return None


def search(
    query: str,
    max_pages: int = 3,
    client: Optional[AudiobookbayClient] = None
) -> list[AudiobookResult]:
    """
    Search Audiobookbay for audiobooks.

    Args:
        query: The search term.
        max_pages: Maximum number of pages to scrape.
        client: Optional client instance (uses default if not provided).

    Returns:
        List of AudiobookResult objects.
    """
    if client is None:
        client = get_client()

    results = []
    print(f"Searching for '{query}' on {client.base_url}...")

    for page in range(1, max_pages + 1):
        url = client.build_search_url(query, page)
        print(f"Fetching page {page}: {url}")

        response = client.get(url)
        if response is None:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.select(".post")

        if not posts:
            print(f"No more results found on page {page}.")
            break

        print(f"Processing {len(posts)} posts on page {page}...")

        for post in posts:
            result = parse_post(post, client)
            if result:
                results.append(result)

        # Rate limiting between pages
        if page < max_pages:
            client.wait()

    return results


def advanced_search(
    query: str,
    options: Optional[AdvancedSearchOptions] = None,
    max_pages: int = 3,
    client: Optional[AudiobookbayClient] = None
) -> list[AudiobookResult]:
    """
    Perform an advanced search on Audiobookbay with category filters.

    Args:
        query: The search term.
        options: Advanced search options (categories, exact match, etc.).
        max_pages: Maximum number of pages to scrape.
        client: Optional client instance (uses default if not provided).

    Returns:
        List of AudiobookResult objects.

    Example:
        # Search for light novels only
        options = AdvancedSearchOptions(
            include_categories=[Category.LIGHT_NOVEL],
            exact_match=True
        )
        results = advanced_search("Arifureta", options)

        # Search excluding adults content
        options = AdvancedSearchOptions(
            exclude_categories=[Category.ADULTS, Category.SEX_SCENES]
        )
        results = advanced_search("romance", options)
    """
    if client is None:
        client = get_client()

    if options is None:
        options = AdvancedSearchOptions()

    results = []
    print(f"Advanced search for '{query}' on {client.base_url}...")

    for page in range(1, max_pages + 1):
        url = client.build_advanced_search_url(query, options.to_query_params(), page)
        print(f"Fetching page {page}: {url}")

        response = client.get(url)
        if response is None:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.select(".post")

        if not posts:
            print(f"No more results found on page {page}.")
            break

        print(f"Processing {len(posts)} posts on page {page}...")

        for post in posts:
            result = parse_post(post, client)
            if result:
                results.append(result)

        # Rate limiting between pages
        if page < max_pages:
            client.wait()

    return results

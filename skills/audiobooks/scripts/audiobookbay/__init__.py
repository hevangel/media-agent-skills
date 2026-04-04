"""
Audiobookbay code snippets for searching and downloading audiobooks.

Usage:
    from audiobookbay_code_snippet import search, enrich_with_magnets
    from audiobookbay_code_snippet import AudiobookbayClient, AudiobookResult

    # Simple search
    results = search("Arifureta", max_pages=2)

    # Get magnet links
    results = enrich_with_magnets(results)

    # Or use custom client
    client = AudiobookbayClient(hostname="audiobookbay.is")
    results = search("Harry Potter", client=client)

    # Advanced search with category filters
    from audiobookbay_code_snippet import advanced_search, AdvancedSearchOptions, Category

    options = AdvancedSearchOptions(
        include_categories=[Category.LIGHT_NOVEL],
        exact_match=True
    )
    results = advanced_search("Arifureta", options)
"""

from .models import AudiobookResult
from .client import AudiobookbayClient, get_client, set_client
from .search import (
    search,
    advanced_search,
    parse_post,
    AdvancedSearchOptions,
    Category,
    SearchIn,
)
from .magnet import extract_magnet_link, enrich_with_magnets

__all__ = [
    "AudiobookResult",
    "AudiobookbayClient",
    "get_client",
    "set_client",
    "search",
    "advanced_search",
    "parse_post",
    "AdvancedSearchOptions",
    "Category",
    "SearchIn",
    "extract_magnet_link",
    "enrich_with_magnets",
]

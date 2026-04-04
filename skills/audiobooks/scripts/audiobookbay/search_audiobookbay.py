"""
Example: Search Audiobookbay for audiobooks and get magnet links.

Usage:
    uv run python audiobooks_organizer/audiobookbay_code_snippet/search_audiobookbay.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audiobookbay_code_snippet import (
    AudiobookbayClient,
    search,
    enrich_with_magnets,
)


def main():
    """Main function to search for Arifureta audiobooks."""
    query = "Arifureta"
    output_file = Path(__file__).parent.parent.parent / "temp" / "arifureta_results.txt"

    print("=" * 60)
    print(f"Searching Audiobookbay for: {query}")
    print("=" * 60)

    # Use the modular API
    results = search(query, max_pages=2)
    results = enrich_with_magnets(results)

    print("\n" + "=" * 60)
    print(f"RESULTS: Found {len(results)} audiobooks")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(result)

    # Save results to a file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Audiobookbay Search Results for: {query}\n")
        f.write("=" * 60 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"--- Result {i} ---\n")
            f.write(str(result))
            f.write("\n\n")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()

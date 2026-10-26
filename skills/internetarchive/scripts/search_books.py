"""
Search for books on archive.org using the advancedsearch API.

Prints identifier, title, creator, year, and lending status for each hit, so
the chosen identifier can be fed straight into capture_book_pages.py:

    uv run python skills/internetarchive/scripts/search_books.py "computer architecture" --creator hennessy
    uv run python skills/internetarchive/scripts/search_books.py --title "alice in wonderland" --year 1865-1930

This replaces manual clicking/typing in the archive.org search UI - one
command per search instead of many browser automation steps.
"""

import argparse
import ipaddress
from urllib.parse import urlparse

import requests


def assert_archive_endpoint(url: str) -> None:
    """SSRF guard: only https archive.org endpoints, never IP/localhost hosts."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "archive.org":
        raise RuntimeError(f"blocked non-archive.org request: {url}")
    try:
        ipaddress.ip_address(parsed.hostname)
        raise RuntimeError("IP-literal hosts are not allowed")
    except ValueError:
        pass  # hostname is a domain, not an IP literal


def build_query(args) -> str:
    """Compose the Lucene-style query from the CLI filters."""
    clauses = []
    if args.query:
        clauses.append(f"({args.query})")
    if args.title:
        clauses.append(f"title:({args.title})")
    if args.creator:
        clauses.append(f"creator:({args.creator})")
    if args.subject:
        clauses.append(f"subject:({args.subject})")
    if args.collection:
        clauses.append(f"collection:({args.collection})")
    if args.year:
        if "-" in args.year:
            lo, hi = args.year.split("-", 1)
            clauses.append(f"year:[{lo} TO {hi}]")
        else:
            clauses.append(f"year:{args.year}")
    clauses.append(f"mediatype:{args.mediatype}")
    return " AND ".join(clauses) or f"mediatype:{args.mediatype}"


def run_search(query: str, rows: int, page: int, sort: str) -> list:
    assert_archive_endpoint("https://archive.org/advancedsearch.php")
    params = {
        "q": query,
        "fl[]": ["identifier", "title", "creator", "year", "downloads",
                 "lending___status", "language"],
        "rows": str(rows),
        "page": str(page),
        "sort[]": [sort],
        "output": "json",
    }
    resp = requests.get("https://archive.org/advancedsearch.php", params=params,
                        timeout=30, headers={"User-Agent": "ai-agents-skill/1.0"})
    resp.raise_for_status()
    return resp.json()["response"]["docs"]


def print_results(docs: list, show_lending: bool) -> None:
    print(f"{len(docs)} result(s)")
    for i, doc in enumerate(docs, 1):
        creator = doc.get("creator")
        if isinstance(creator, list):
            creator = "; ".join(str(c) for c in creator)
        creator = str(creator or "?")[:60]
        year = doc.get("year") or "?"
        title = str(doc.get("title") or doc["identifier"])[:90]
        print(f"\n[{i}] {doc['identifier']}")
        print(f"    {title} ({year}) by {creator}")
        extras = []
        if show_lending:
            status = doc.get("lending___status")
            if status:
                flags = status if isinstance(status, list) else [status]
                avail = [f for f in flags if f.startswith("available")]
                if avail:
                    extras.append("lending: " + ", ".join(avail))
                else:
                    extras.append(f"lending: {flags[0]}")
        if doc.get("downloads"):
            extras.append(f"{doc['downloads']} downloads")
        if doc.get("language"):
            lang = doc["language"]
            extras.append(lang if isinstance(lang, str) else lang[0])
        if extras:
            print(f"    {' | '.join(extras)}")


def main():
    parser = argparse.ArgumentParser(
        description="Search books on archive.org (advancedsearch API)"
    )
    parser.add_argument("query", nargs="?", default="",
                        help="Free-text query (Lucene syntax allowed)")
    parser.add_argument("--title", default=None, help="Match title")
    parser.add_argument("--creator", default=None, help="Match author/creator")
    parser.add_argument("--subject", default=None, help="Match subject/topic")
    parser.add_argument("--collection", default=None, help="Match collection")
    parser.add_argument("--year", default=None,
                        help="Single year (1990) or range (1990-1995)")
    parser.add_argument("--mediatype", default="texts",
                        help="mediatype filter (default: texts)")
    parser.add_argument("--rows", type=int, default=10,
                        help="Results per page (default 10, max 100)")
    parser.add_argument("--page", type=int, default=1, help="Result page")
    parser.add_argument("--sort", default="downloads desc",
                        help="Sort, e.g. 'downloads desc' or 'year asc'")
    parser.add_argument("--ids", action="store_true",
                        help="Print identifiers only (for scripting)")
    args = parser.parse_args()

    if args.rows > 100:
        args.rows = 100

    query = build_query(args)
    print(f"Searching archive.org: {query}")
    try:
        docs = run_search(query, args.rows, args.page, args.sort)
    except requests.RequestException as exc:
        print(f"Error: search request failed - {exc}")
        raise SystemExit(1)

    if args.ids:
        for doc in docs:
            print(doc["identifier"])
        return
    print_results(docs, show_lending=True)


if __name__ == "__main__":
    main()

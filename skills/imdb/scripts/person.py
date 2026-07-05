"""
Get celebrity/person profile from IMDB by name or ID.
Uses IMDB suggestion API to find the person, then GraphQL for details.
"""

import argparse
import json
import sys

try:
    from imdb_client import suggest_search, graphql_get_person
except ImportError:
    from .imdb_client import suggest_search, graphql_get_person


def person_by_name(name):
    """Look up a person by name."""
    print(f"Looking up person '{name}' on IMDB...")
    results = suggest_search(name)
    results = [r for r in results if r.get("id", "").startswith("nm")]
    if not results:
        print("No results found.")
        return {}

    imdb_id = results[0]["id"]
    print(f"Found match: {results[0]['name']} ({imdb_id}), fetching details...")
    data = graphql_get_person(imdb_id)
    if data:
        print(f"Found: {data.get('name')}")
        return data

    print("Could not retrieve details.")
    return {}


def person_by_id(imdb_id):
    """Look up a person by IMDB ID."""
    print(f"Looking up person ID '{imdb_id}' on IMDB...")
    data = graphql_get_person(imdb_id)
    if data:
        print(f"Found: {data.get('name')}")
        return data

    print("Not found.")
    return {}


def display_person(data):
    """Pretty print person info."""
    print(f"\n  Name:      {data.get('name', 'N/A')}")
    print(f"  URL:       {data.get('url', 'N/A')}")
    print(f"  Job:       {data.get('jobTitle', 'N/A')}")
    print(f"  Born:      {data.get('birthDate', 'N/A')}")

    desc = data.get("description", "")
    if desc:
        print(f"  Bio:       {desc[:200]}{'...' if len(desc) > 200 else ''}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get person profile from IMDB")
    parser.add_argument("name", nargs="?", help="Person name")
    parser.add_argument("--id", help="IMDB person ID (e.g. nm0000093)")
    args = parser.parse_args()

    if args.id:
        data = person_by_id(args.id)
    elif args.name:
        data = person_by_name(args.name)
    else:
        print("Usage: python person.py <name> OR python person.py --id <imdb_id>")
        sys.exit(1)

    display_person(data)

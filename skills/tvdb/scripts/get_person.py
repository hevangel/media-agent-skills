"""
Get person details from TheTVDB by ID.
"""

import argparse
import json
import sys

try:
    from tvdb_client import get_client
except ImportError:
    from .tvdb_client import get_client


def get_person(person_id, extended=False):
    """Look up a person by TVDB ID."""
    print(f"Looking up TVDB person ID {person_id} (extended={extended})...")
    tvdb = get_client()
    if extended:
        data = tvdb.get_person_extended(person_id)
    else:
        data = tvdb.get_person(person_id)
    if data:
        print(f"Found: {data.get('name')}")
        return data
    print("Not found.")
    return {}


def display_info(data, extended=False):
    """Pretty print person info."""
    print(f"\n  Name:        {data.get('name', 'N/A')}")
    print(f"  TVDB ID:     {data.get('id', 'N/A')}")
    print(f"  Birth:       {data.get('birth', 'N/A')}")
    print(f"  Death:       {data.get('death', 'N/A')}")
    print(f"  Gender:      {data.get('gender', 'N/A')}")
    print(f"  Score:       {data.get('score', 'N/A')}")

    if extended:
        characters = data.get("characters", [])
        if characters:
            print(f"\n  Roles ({len(characters)}):")
            for c in characters[:15]:
                series = c.get("seriesName") or c.get("movieName") or "Unknown"
                role = c.get("name", "Unknown")
                print(f"    {role} in {series}")
            if len(characters) > 15:
                print(f"    ... and {len(characters) - 15} more")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get person info from TheTVDB")
    parser.add_argument("id", type=int, help="TVDB person ID")
    parser.add_argument("--extended", action="store_true", help="Get extended info with roles")
    args = parser.parse_args()

    data = get_person(args.id, extended=args.extended)
    display_info(data, extended=args.extended)

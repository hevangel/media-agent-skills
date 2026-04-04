"""
Analyze EPUB metadata to find missing or incomplete information.
Demonstrates metadata validation and reporting.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def check_missing_metadata(metadata_json_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Analyze EPUB metadata to find files with missing title or author.
    
    Args:
        metadata_json_path: Path to the JSON file containing EPUB metadata
        
    Returns:
        Dictionary with keys 'missing_both', 'missing_title', 'missing_author'
    """
    with open(metadata_json_path, encoding="utf-8") as f:
        data = json.load(f)
    
    # Find EPUBs with missing title or author
    missing_title = []
    missing_author = []
    missing_both = []
    
    for item in data:
        has_title = item.get('title') and item.get('title') != "None"
        has_author = item.get('creator') and item.get('creator') != "None"
        
        if not has_title and not has_author:
            missing_both.append(item)
        elif not has_title:
            missing_title.append(item)
        elif not has_author:
            missing_author.append(item)
    
    return {
        'missing_both': missing_both,
        'missing_title': missing_title,
        'missing_author': missing_author,
        'total': len(data)
    }


def print_missing_metadata_report(results: Dict[str, List[Dict[str, Any]]]):
    """
    Print a formatted report of missing metadata.
    
    Args:
        results: Dictionary from check_missing_metadata()
    """
    print(f"Total EPUBs scanned: {results['total']}")
    print(f"\nEPUBs missing BOTH title and author: {len(results['missing_both'])}")
    print(f"EPUBs missing ONLY title: {len(results['missing_title'])}")
    print(f"EPUBs missing ONLY author: {len(results['missing_author'])}")
    
    total_issues = len(results['missing_both']) + len(results['missing_title']) + len(results['missing_author'])
    print(f"\nTotal with issues: {total_issues}")
    
    if results['missing_both']:
        print("\n" + "="*80)
        print("EPUBs missing BOTH title and author:")
        print("="*80)
        for item in results['missing_both']:
            print(f"\nFile: {item['file_name']}")
            print(f"Path: {item['file_path']}")
    
    if results['missing_title']:
        print("\n" + "="*80)
        print("EPUBs missing ONLY title:")
        print("="*80)
        for item in results['missing_title']:
            print(f"\nFile: {item['file_name']}")
            print(f"Author: {item.get('creator', 'N/A')}")
            print(f"Path: {item['file_path']}")
    
    if results['missing_author']:
        print("\n" + "="*80)
        print("EPUBs missing ONLY author:")
        print("="*80)
        for item in results['missing_author']:
            print(f"\nFile: {item['file_name']}")
            print(f"Title: {item.get('title', 'N/A')}")
            print(f"Path: {item['file_path']}")


def main():
    """Check for missing metadata in EPUB files."""
    metadata_file = Path(__file__).parent.parent.parent / "temp" / "epub_metadata.json"
    
    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}")
        print("Please run extract_metadata.py first to generate the metadata file.")
        return
    
    print("Analyzing EPUB metadata...")
    results = check_missing_metadata(metadata_file)
    print_missing_metadata_report(results)


if __name__ == "__main__":
    main()

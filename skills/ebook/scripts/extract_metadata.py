"""
Extract metadata from EPUB files and save to JSON.
Demonstrates reading EPUB metadata using ebooklib.
"""

import json
import ebooklib
from ebooklib import epub
from pathlib import Path
from typing import Dict, List, Any
import sys


def extract_epub_metadata(epub_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from an EPUB file.
    
    Args:
        epub_path: Path to the EPUB file
        
    Returns:
        Dictionary containing metadata fields or error information
    """
    try:
        book = epub.read_epub(str(epub_path))
        
        metadata = {
            "file_path": str(epub_path),
            "file_name": epub_path.name,
            "file_size": epub_path.stat().st_size,
        }
        
        # Extract common Dublin Core metadata fields
        metadata["title"] = book.get_metadata("DC", "title")
        metadata["creator"] = book.get_metadata("DC", "creator")
        metadata["language"] = book.get_metadata("DC", "language")
        metadata["identifier"] = book.get_metadata("DC", "identifier")
        metadata["publisher"] = book.get_metadata("DC", "publisher")
        metadata["date"] = book.get_metadata("DC", "date")
        metadata["subject"] = book.get_metadata("DC", "subject")
        metadata["description"] = book.get_metadata("DC", "description")
        metadata["rights"] = book.get_metadata("DC", "rights")
        metadata["contributor"] = book.get_metadata("DC", "contributor")
        
        # Flatten metadata lists to single values or lists of strings
        for key, value in metadata.items():
            if isinstance(value, list) and len(value) > 0:
                # Extract the actual text from tuple format
                metadata[key] = [str(item[0]) if isinstance(item, tuple) else str(item) for item in value]
                if len(metadata[key]) == 1:
                    metadata[key] = metadata[key][0]
            elif isinstance(value, list):
                metadata[key] = None
        
        return metadata
        
    except Exception as e:
        return {
            "file_path": str(epub_path),
            "file_name": epub_path.name,
            "error": str(e)
        }


def scan_epub_files(directory: Path, show_progress: bool = True) -> List[Dict[str, Any]]:
    """
    Scan directory recursively for EPUB files and extract their metadata.
    
    Args:
        directory: Path to directory to scan
        show_progress: Whether to print progress messages
        
    Returns:
        List of metadata dictionaries
    """
    epub_metadata_list = []
    
    if show_progress:
        print(f"Scanning directory: {directory}")
    
    epub_files = list(directory.rglob("*.epub"))
    total_files = len(epub_files)
    
    if show_progress:
        print(f"Found {total_files} EPUB files")
    
    for idx, epub_file in enumerate(epub_files, 1):
        if show_progress:
            print(f"Processing [{idx}/{total_files}]: {epub_file.name}")
        metadata = extract_epub_metadata(epub_file)
        epub_metadata_list.append(metadata)
    
    return epub_metadata_list


def main():
    """Extract metadata from all EPUBs in a directory and save to JSON."""
    # Directory containing EPUB files
    epub_directory = Path(r"E:\ebook\Calibre Library")
    
    if not epub_directory.exists():
        print(f"Error: Directory does not exist: {epub_directory}")
        sys.exit(1)
    
    # Extract metadata from all EPUB files
    print("Starting EPUB metadata extraction...")
    epub_metadata = scan_epub_files(epub_directory)
    
    # Save to JSON file
    output_file = Path(__file__).parent.parent.parent / "temp" / "epub_metadata.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSaving metadata to: {output_file}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(epub_metadata, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully extracted metadata from {len(epub_metadata)} EPUB files")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()

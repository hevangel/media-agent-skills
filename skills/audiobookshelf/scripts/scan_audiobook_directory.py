"""
Scan Local Audiobook Directory
Scan audiobook directories and extract author/title information.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# Audio file extensions to look for
AUDIO_EXTENSIONS = {'.m4a', '.m4b', '.mp3', '.flac', '.ogg', '.opus'}

# Cover file patterns to check
COVER_PATTERNS = [
    "cover.jpg", "cover.jpeg", "cover.png",
    "folder.jpg", "folder.jpeg", "folder.png",
    "Cover.jpg", "Cover.jpeg", "Cover.png",
    "Folder.jpg", "Folder.jpeg", "Folder.png"
]


@dataclass
class AudiobookInfo:
    """Information about an audiobook."""
    author: str
    title: str
    path: str
    has_audio: bool = False
    audio_files: List[str] = None
    has_cover: bool = False
    cover_file: str = None
    
    def __post_init__(self):
        if self.audio_files is None:
            self.audio_files = []


# =============================================================================
# BASIC DIRECTORY SCANNING
# =============================================================================
def scan_audiobooks(audiobook_root: str = os.getenv("AUDIOBOOKS_PATH", "audiobooks")) -> List[Dict[str, Any]]:
    """
    Scan audiobook directory with Author/Title structure.
    
    Expected structure:
        audiobook_root/
            Author Name/
                Book Title/
                    audiobook.m4b
                    cover.jpg
    
    Args:
        audiobook_root: Root directory containing audiobooks
        
    Returns:
        List of audiobook dictionaries
    """
    audiobooks = []
    
    if not os.path.exists(audiobook_root):
        print(f"Directory not found: {audiobook_root}")
        return audiobooks
    
    print(f"Scanning audiobooks in: {audiobook_root}")
    
    # Walk through author directories
    try:
        for author_name in os.listdir(audiobook_root):
            author_path = os.path.join(audiobook_root, author_name)
            
            if not os.path.isdir(author_path):
                continue
            
            # Walk through title directories
            try:
                for title_name in os.listdir(author_path):
                    title_path = os.path.join(author_path, title_name)
                    
                    if not os.path.isdir(title_path):
                        continue
                    
                    # Check for audio files
                    has_audio = False
                    audio_files = []
                    
                    try:
                        for file_name in os.listdir(title_path):
                            file_path = os.path.join(title_path, file_name)
                            if os.path.isfile(file_path):
                                _, ext = os.path.splitext(file_name.lower())
                                if ext in AUDIO_EXTENSIONS:
                                    has_audio = True
                                    audio_files.append(file_name)
                    except PermissionError:
                        continue
                    
                    if has_audio:
                        # Check for cover
                        has_cover = False
                        cover_file = None
                        for pattern in COVER_PATTERNS:
                            cover_path = os.path.join(title_path, pattern)
                            if os.path.exists(cover_path):
                                has_cover = True
                                cover_file = pattern
                                break
                        
                        audiobooks.append({
                            'author': author_name,
                            'title': title_name,
                            'path': title_path,
                            'has_audio': True,
                            'audio_files': audio_files,
                            'has_cover': has_cover,
                            'cover_file': cover_file
                        })
                        
            except PermissionError:
                print(f"Permission denied: {author_path}")
                
    except Exception as e:
        print(f"Error scanning: {e}")
    
    print(f"Found {len(audiobooks)} audiobooks")
    return audiobooks


def scan_root_files(root_dir: str) -> List[Dict[str, Any]]:
    """
    Scan for audio files directly in the root directory (not in subdirectories).
    Useful for finding misplaced audiobook files.
    
    Args:
        root_dir: Directory to scan
        
    Returns:
        List of audio file info dictionaries
    """
    if not os.path.exists(root_dir):
        print(f"Directory not found: {root_dir}")
        return []
    
    root_files = []
    
    try:
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            
            if os.path.isfile(item_path):
                _, ext = os.path.splitext(item.lower())
                if ext in AUDIO_EXTENSIONS:
                    root_files.append({
                        'name': item,
                        'path': item_path,
                        'extension': ext,
                        'size': os.path.getsize(item_path),
                        'size_mb': os.path.getsize(item_path) / (1024 * 1024)
                    })
    except Exception as e:
        print(f"Error scanning: {e}")
    
    print(f"Found {len(root_files)} audio files in root")
    return root_files


# =============================================================================
# FILTERING AND ANALYSIS
# =============================================================================
def get_audiobooks_missing_covers(audiobooks: List[Dict]) -> List[Dict]:
    """
    Filter audiobooks that don't have cover images.
    
    Args:
        audiobooks: List of audiobook dicts from scan_audiobooks()
        
    Returns:
        Filtered list of audiobooks without covers
    """
    return [book for book in audiobooks if not book.get('has_cover', False)]


def get_author_statistics(audiobooks: List[Dict]) -> Dict[str, Any]:
    """
    Get statistics grouped by author.
    
    Args:
        audiobooks: List of audiobook dicts
        
    Returns:
        Dict with author statistics
    """
    author_stats = {}
    
    for book in audiobooks:
        author = book['author']
        if author not in author_stats:
            author_stats[author] = {
                'audiobook_count': 0,
                'titles': [],
                'missing_covers': 0
            }
        
        author_stats[author]['audiobook_count'] += 1
        author_stats[author]['titles'].append(book['title'])
        
        if not book.get('has_cover', False):
            author_stats[author]['missing_covers'] += 1
    
    return author_stats


# =============================================================================
# AUTHOR NAME CLEANUP
# =============================================================================
def clean_author_name(author: str) -> str:
    """
    Clean up common author name issues.
    
    Args:
        author: Original author name
        
    Returns:
        Cleaned author name
    """
    fixed = author
    
    # Fix "LastName, FirstName" format
    if ', ' in author and not any(x in author.lower() for x in ['jr.', 'sr.', 'iii', 'ii']):
        parts = author.split(', ', 1)
        if len(parts) == 2:
            fixed = f"{parts[1]} {parts[0]}"
    
    # Remove academic titles
    for suffix in [', Ph.D', ', Dr.', ', MD', ', M.D.']:
        if suffix in fixed:
            fixed = fixed.split(suffix)[0]
    
    # Remove role indicators
    for suffix in [' - Forward', ' - Foreword', ' - Introduction', ' - Editor']:
        if suffix in fixed:
            fixed = fixed.split(suffix)[0]
    
    return fixed.strip()


def apply_author_fixes(audiobooks: List[Dict]) -> List[Dict]:
    """
    Apply author name fixes to audiobook list.
    
    Args:
        audiobooks: List of audiobook dicts
        
    Returns:
        Updated list with cleaned author names
    """
    for book in audiobooks:
        original = book['author']
        book['original_author'] = original
        book['author'] = clean_author_name(original)
        
        if original != book['author']:
            print(f"Fixed: '{original}' → '{book['author']}'")
    
    return audiobooks


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================
def export_to_json(audiobooks: List[Dict], output_file: str):
    """
    Export audiobook data to JSON file.
    
    Args:
        audiobooks: List of audiobook dicts
        output_file: Output JSON file path
    """
    # Get unique authors
    authors = set(book['author'] for book in audiobooks)
    
    output_data = {
        'summary': {
            'total_audiobooks': len(audiobooks),
            'total_authors': len(authors),
            'scan_date': datetime.now().isoformat(),
        },
        'author_statistics': get_author_statistics(audiobooks),
        'audiobooks': audiobooks
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"Exported {len(audiobooks)} audiobooks to: {output_file}")


def print_summary(audiobooks: List[Dict]):
    """
    Print a summary of scanned audiobooks.
    
    Args:
        audiobooks: List of audiobook dicts
    """
    authors = set(book['author'] for book in audiobooks)
    missing_covers = len([b for b in audiobooks if not b.get('has_cover', False)])
    
    print("\n" + "=" * 50)
    print("AUDIOBOOK SCAN SUMMARY")
    print("=" * 50)
    print(f"Total audiobooks: {len(audiobooks)}")
    print(f"Total authors: {len(authors)}")
    print(f"Missing covers: {missing_covers}")
    print("=" * 50)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    # Example: Scan main audiobooks directory
    AUDIOBOOKS_ROOT = os.getenv("AUDIOBOOKS_PATH", "audiobooks")
    
    print("=== Scanning Audiobooks ===\n")
    audiobooks = scan_audiobooks(AUDIOBOOKS_ROOT)
    print_summary(audiobooks)
    
    # Export to JSON
    # export_to_json(audiobooks, "audiobook_scan.json")
    
    # Find audiobooks missing covers
    missing_covers = get_audiobooks_missing_covers(audiobooks)
    print(f"\nAudiobooks missing covers: {len(missing_covers)}")
    for book in missing_covers[:5]:  # Show first 5
        print(f"  - {book['author']} / {book['title']}")
    
    # Example: Scan root for misplaced files
    # print("\n=== Scanning Root Directory ===\n")
    # root_files = scan_root_files(os.getenv("AUDIOBOOKS_PATH", "audiobooks"))
    # for f in root_files:
    #     print(f"  {f['name']} ({f['size_mb']:.1f} MB)")

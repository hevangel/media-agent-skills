"""
Update Local Audio File Metadata
Uses mutagen library to update ID3/MP4/FLAC/OGG tags in audio files.
"""

import os
from pathlib import Path
from typing import Optional

try:
    from mutagen.id3 import ID3, TPE1, TPE2, TIT2, TALB, TDRC, TCON, TRCK
    from mutagen.mp4 import MP4
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("WARNING: mutagen library not available. Install with: uv add mutagen")


# =============================================================================
# AUDIO FILE EXTENSIONS
# =============================================================================
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.m4b', '.flac', '.ogg', '.opus'}


# =============================================================================
# UPDATE METADATA
# =============================================================================
def update_audio_metadata(
    file_path: str,
    author: str = None,
    title: str = None,
    album: str = None,
    genre: str = None,
    year: str = None,
    track: str = None
) -> bool:
    """
    Update metadata for a single audio file.
    
    Args:
        file_path: Path to the audio file
        author: Artist/Author name
        title: Track title
        album: Album/Book title
        genre: Genre
        year: Publication year
        track: Track number
        
    Returns:
        True if update was successful
    """
    if not MUTAGEN_AVAILABLE:
        print(f"Cannot update {file_path}: mutagen not available")
        return False
    
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is None:
            print(f"Could not read audio file: {file_path}")
            return False
        
        # Handle different file types
        if isinstance(audio_file, MP4):
            # M4A/M4B files
            if audio_file.tags is None:
                audio_file.add_tags()
            
            if author:
                audio_file.tags['\xa9ART'] = [author]  # Artist
                audio_file.tags['aART'] = [author]     # Album artist
            if title:
                audio_file.tags['\xa9nam'] = [title]   # Title
            if album:
                audio_file.tags['\xa9alb'] = [album]   # Album
            if genre:
                audio_file.tags['\xa9gen'] = [genre]   # Genre
            if year:
                audio_file.tags['\xa9day'] = [year]    # Year
            if track:
                audio_file.tags['trkn'] = [(int(track), 0)]  # Track number
            
            audio_file.save()
            return True
            
        elif hasattr(audio_file, 'tags'):
            # MP3 with ID3 tags
            if audio_file.tags is None:
                audio_file.add_tags()
            
            if author:
                audio_file.tags['TPE1'] = TPE1(encoding=3, text=[author])
                audio_file.tags['TPE2'] = TPE2(encoding=3, text=[author])
            if title:
                audio_file.tags['TIT2'] = TIT2(encoding=3, text=[title])
            if album:
                audio_file.tags['TALB'] = TALB(encoding=3, text=[album])
            if genre:
                audio_file.tags['TCON'] = TCON(encoding=3, text=[genre])
            if year:
                audio_file.tags['TDRC'] = TDRC(encoding=3, text=[year])
            if track:
                audio_file.tags['TRCK'] = TRCK(encoding=3, text=[track])
            
            audio_file.save()
            return True
            
        elif isinstance(audio_file, FLAC):
            if audio_file.tags is None:
                audio_file.add_tags()
            
            if author:
                audio_file.tags['ARTIST'] = [author]
                audio_file.tags['ALBUMARTIST'] = [author]
            if title:
                audio_file.tags['TITLE'] = [title]
            if album:
                audio_file.tags['ALBUM'] = [album]
            if genre:
                audio_file.tags['GENRE'] = [genre]
            if year:
                audio_file.tags['DATE'] = [year]
            if track:
                audio_file.tags['TRACKNUMBER'] = [track]
            
            audio_file.save()
            return True
            
        elif isinstance(audio_file, OggVorbis):
            if audio_file.tags is None:
                audio_file.add_tags()
            
            if author:
                audio_file.tags['ARTIST'] = [author]
                audio_file.tags['ALBUMARTIST'] = [author]
            if title:
                audio_file.tags['TITLE'] = [title]
            if album:
                audio_file.tags['ALBUM'] = [album]
            if genre:
                audio_file.tags['GENRE'] = [genre]
            if year:
                audio_file.tags['DATE'] = [year]
            if track:
                audio_file.tags['TRACKNUMBER'] = [track]
            
            audio_file.save()
            return True
        
        else:
            print(f"Unsupported file type for {file_path}: {type(audio_file)}")
            return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


# =============================================================================
# READ METADATA
# =============================================================================
def read_audio_metadata(file_path: str) -> dict:
    """
    Read metadata from an audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dict with metadata fields
    """
    if not MUTAGEN_AVAILABLE:
        return {"error": "mutagen not available"}
    
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is None:
            return {"error": "Could not read file"}
        
        result = {
            "format": type(audio_file).__name__,
            "artist": None,
            "title": None,
            "album": None,
        }
        
        if hasattr(audio_file, 'tags') and audio_file.tags:
            # Try different tag formats
            if 'TPE1' in audio_file.tags:  # ID3
                result['artist'] = str(audio_file.tags['TPE1'])
            elif '\xa9ART' in audio_file.tags:  # MP4
                result['artist'] = str(audio_file.tags['\xa9ART'][0])
            elif 'ARTIST' in audio_file.tags:  # FLAC/OGG
                result['artist'] = str(audio_file.tags['ARTIST'][0])
            
            if 'TIT2' in audio_file.tags:
                result['title'] = str(audio_file.tags['TIT2'])
            elif '\xa9nam' in audio_file.tags:
                result['title'] = str(audio_file.tags['\xa9nam'][0])
            elif 'TITLE' in audio_file.tags:
                result['title'] = str(audio_file.tags['TITLE'][0])
            
            if 'TALB' in audio_file.tags:
                result['album'] = str(audio_file.tags['TALB'])
            elif '\xa9alb' in audio_file.tags:
                result['album'] = str(audio_file.tags['\xa9alb'][0])
            elif 'ALBUM' in audio_file.tags:
                result['album'] = str(audio_file.tags['ALBUM'][0])
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# BATCH OPERATIONS
# =============================================================================
def get_audio_files(directory: str) -> list:
    """
    Get all audio files in a directory.
    
    Args:
        directory: Directory path to scan
        
    Returns:
        List of audio file paths
    """
    audio_files = []
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return audio_files
    
    try:
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file_name.lower())
                if ext in AUDIO_EXTENSIONS:
                    audio_files.append(file_path)
    except PermissionError:
        print(f"Permission denied: {directory}")
    
    return audio_files


def update_directory_metadata(
    directory: str,
    author: str,
    title: str = None,
    max_files: int = None
) -> tuple:
    """
    Update metadata for all audio files in a directory.
    
    Args:
        directory: Directory containing audio files
        author: Author/Artist name to set
        title: Optional title (usually left as-is for chapter files)
        max_files: Maximum number of files to update (None for all)
        
    Returns:
        Tuple of (success_count, total_count)
    """
    audio_files = get_audio_files(directory)
    
    if max_files:
        audio_files = audio_files[:max_files]
    
    success_count = 0
    
    for file_path in audio_files:
        if update_audio_metadata(file_path, author=author, title=title):
            success_count += 1
            print(f"✓ {os.path.basename(file_path)}")
        else:
            print(f"✗ {os.path.basename(file_path)}")
    
    return success_count, len(audio_files)


def verify_directory_metadata(directory: str):
    """
    Verify and display metadata for all audio files in a directory.
    
    Args:
        directory: Directory to verify
    """
    audio_files = get_audio_files(directory)
    
    print(f"Verifying {len(audio_files)} audio files in: {directory}\n")
    
    for file_path in audio_files:
        file_name = os.path.basename(file_path)
        metadata = read_audio_metadata(file_path)
        
        print(f"📄 {file_name}")
        print(f"   Format: {metadata.get('format', 'Unknown')}")
        print(f"   Artist: {metadata.get('artist', 'N/A')}")
        print(f"   Title: {metadata.get('title', 'N/A')}")
        print(f"   Album: {metadata.get('album', 'N/A')}")
        print()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    # Check if mutagen is available
    print(f"Mutagen available: {MUTAGEN_AVAILABLE}\n")
    
    if MUTAGEN_AVAILABLE:
        # Example: Update a single file
        # update_audio_metadata(
        #     "path/to/audiobook.m4b",
        #     author="Isaac Asimov",
        #     title="Foundation",
        #     album="Foundation"
        # )
        
        # Example: Update all files in a directory
        # success, total = update_directory_metadata(
        #     os.getenv("AUDIOBOOKS_PATH", "audiobooks") + "/Isaac Asimov/Foundation",
        #     author="Isaac Asimov",
        #     max_files=3  # Limit for safety
        # )
        # print(f"\nUpdated {success}/{total} files")
        
        # Example: Verify metadata
        # verify_directory_metadata(os.getenv("AUDIOBOOKS_PATH", "audiobooks") + "/Isaac Asimov/Foundation")
        
        print("See examples in the code for usage patterns.")
    else:
        print("Install mutagen with: uv add mutagen")

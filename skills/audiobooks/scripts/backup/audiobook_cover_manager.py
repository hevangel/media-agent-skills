"""
Audiobook Cover Manager
Scans audiobook directories, identifies missing covers (file and embedded), and downloads them.
"""

import os
import json
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import time

try:
    from mutagen import File as MutagenFile
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.mp3 import MP3
    from mutagen.id3 import APIC
    from mutagen.flac import FLAC, Picture
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen library not available. Install with: uv add mutagen")


@dataclass
class AudiobookInfo:
    author: str
    title: str
    path: str
    has_cover: bool
    audio_files: List[str]
    cover_file: Optional[str] = None
    has_embedded_cover: bool = False
    embedded_in_file: Optional[str] = None


class AudiobookCoverManager:
    def __init__(self, audiobooks_root: str = os.getenv("AUDIOBOOKS_PATH", "audiobooks")):
        self.audiobooks_root = Path(audiobooks_root)
        self.cover_patterns = [
            "cover.jpg", "cover.jpeg", "cover.png",
            "folder.jpg", "folder.jpeg", "folder.png",
            "Cover.jpg", "Cover.jpeg", "Cover.png",
            "Folder.jpg", "Folder.jpeg", "Folder.png"
        ]
        self.audio_extensions = [".m4a", ".m4b", ".mp3", ".flac", ".ogg"]
        self.audiobooks: List[AudiobookInfo] = []
    
    def check_embedded_cover(self, audio_file_path: Path) -> bool:
        """Check if an audio file has embedded cover art."""
        if not MUTAGEN_AVAILABLE:
            return False
        
        try:
            audio = MutagenFile(str(audio_file_path))
            if audio is None:
                return False
            
            # Check for MP4/M4A/M4B files
            if isinstance(audio, MP4):
                return audio.tags and 'covr' in audio.tags
            
            # Check for MP3 files
            elif isinstance(audio, MP3):
                if audio.tags:
                    for tag in audio.tags.values():
                        if isinstance(tag, APIC):
                            return True
                return False
            
            # Check for FLAC files
            elif isinstance(audio, FLAC):
                return len(audio.pictures) > 0 if hasattr(audio, 'pictures') else False
            
            # Check for OGG files
            elif isinstance(audio, OggVorbis):
                if audio.tags:
                    for key in audio.tags.keys():
                        if key.lower().startswith('metadata_block_picture'):
                            return True
                return False
            
            return False
            
        except Exception as e:
            # Silently fail for corrupted or unsupported files
            return False
    
    def scan_audiobooks(self) -> List[AudiobookInfo]:
        """Scan the audiobooks directory and identify all audiobooks."""
        print(f"Scanning audiobooks in {self.audiobooks_root}...")
        if MUTAGEN_AVAILABLE:
            print("Mutagen available - will check for embedded covers")
        else:
            print("Mutagen not available - skipping embedded cover check")
        
        self.audiobooks = []
        
        # Iterate through author directories
        for author_dir in self.audiobooks_root.iterdir():
            if not author_dir.is_dir():
                continue
                
            author_name = author_dir.name
            
            # Iterate through title directories
            for title_dir in author_dir.iterdir():
                if not title_dir.is_dir():
                    continue
                    
                title_name = title_dir.name
                
                # Check for cover files
                cover_file = None
                for pattern in self.cover_patterns:
                    cover_path = title_dir / pattern
                    if cover_path.exists():
                        cover_file = pattern
                        break
                
                # Find audio files
                audio_files = []
                for file in title_dir.iterdir():
                    if file.is_file() and file.suffix.lower() in self.audio_extensions:
                        audio_files.append(file.name)
                
                # Check for embedded cover in first audio file
                has_embedded_cover = False
                embedded_in_file = None
                if audio_files and MUTAGEN_AVAILABLE:
                    first_audio = title_dir / audio_files[0]
                    has_embedded_cover = self.check_embedded_cover(first_audio)
                    if has_embedded_cover:
                        embedded_in_file = audio_files[0]
                
                # Only include if there are audio files
                if audio_files:
                    audiobook = AudiobookInfo(
                        author=author_name,
                        title=title_name,
                        path=str(title_dir),
                        has_cover=cover_file is not None,
                        audio_files=audio_files,
                        cover_file=cover_file,
                        has_embedded_cover=has_embedded_cover,
                        embedded_in_file=embedded_in_file
                    )
                    self.audiobooks.append(audiobook)
        
        print(f"Found {len(self.audiobooks)} audiobooks")
        return self.audiobooks
    
    def get_missing_covers(self) -> List[AudiobookInfo]:
        """Get list of audiobooks without covers (neither file nor embedded)."""
        missing = [ab for ab in self.audiobooks if not ab.has_cover and not ab.has_embedded_cover]
        print(f"Found {len(missing)} audiobooks missing covers (file and embedded)")
        return missing
    
    def save_scan_results(self, filename: str = "audiobook_scan_results.json"):
        """Save scan results to a JSON file."""
        results = {
            "total_audiobooks": len(self.audiobooks),
            "with_file_covers": sum(1 for ab in self.audiobooks if ab.has_cover),
            "with_embedded_covers": sum(1 for ab in self.audiobooks if ab.has_embedded_cover),
            "with_any_cover": sum(1 for ab in self.audiobooks if ab.has_cover or ab.has_embedded_cover),
            "without_covers": sum(1 for ab in self.audiobooks if not ab.has_cover and not ab.has_embedded_cover),
            "audiobooks": [
                {
                    "author": ab.author,
                    "title": ab.title,
                    "path": ab.path,
                    "has_cover": ab.has_cover,
                    "cover_file": ab.cover_file,
                    "has_embedded_cover": ab.has_embedded_cover,
                    "embedded_in_file": ab.embedded_in_file,
                    "audio_file_count": len(ab.audio_files),
                    "audio_files": ab.audio_files[:3]  # First 3 files for reference
                }
                for ab in self.audiobooks
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Scan results saved to {filename}")
        return results
    
    def generate_report(self) -> str:
        """Generate a summary report."""
        total = len(self.audiobooks)
        with_file_covers = sum(1 for ab in self.audiobooks if ab.has_cover)
        with_embedded = sum(1 for ab in self.audiobooks if ab.has_embedded_cover)
        with_any = sum(1 for ab in self.audiobooks if ab.has_cover or ab.has_embedded_cover)
        without_covers = total - with_any
        
        report = f"""
# Audiobook Cover Scan Report

## Summary
- Total Audiobooks: {total}
- With File Covers: {with_file_covers} ({with_file_covers/total*100:.1f}%)
- With Embedded Covers: {with_embedded} ({with_embedded/total*100:.1f}%)
- With Any Cover: {with_any} ({with_any/total*100:.1f}%)
- Missing All Covers: {without_covers} ({without_covers/total*100:.1f}%)

## Audiobooks Missing Covers (File and Embedded)
"""
        
        missing = self.get_missing_covers()
        for ab in sorted(missing, key=lambda x: (x.author, x.title)):
            report += f"\n- **{ab.author}** - {ab.title}\n  Path: `{ab.path}`\n  Audio files: {len(ab.audio_files)}"
        
        return report


def main():
    """Main entry point."""
    manager = AudiobookCoverManager()
    
    # Scan audiobooks
    manager.scan_audiobooks()
    
    # Save results
    results = manager.save_scan_results()
    
    # Generate report
    report = manager.generate_report()
    
    # Save report
    with open("audiobook_cover_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total: {results['total_audiobooks']}")
    print(f"  With file covers: {results['with_file_covers']}")
    print(f"  With embedded covers: {results['with_embedded_covers']}")
    print(f"  With any cover: {results['with_any_cover']}")
    print(f"  Missing all covers: {results['without_covers']}")


if __name__ == "__main__":
    main()

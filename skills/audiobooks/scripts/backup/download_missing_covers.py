"""
Interactive Cover Downloader with Web Search
Downloads covers for audiobooks missing them.
"""

import json
import os
import sys
import requests
from pathlib import Path
from typing import List, Dict, Optional
import base64

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


def load_missing_audiobooks():
    """Load audiobooks missing covers."""
    with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing = [ab for ab in data['audiobooks'] if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
    return missing


def download_image(url: str, save_path: str) -> bool:
    """Download image from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ Downloaded: {len(response.content) / 1024:.1f} KB")
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def embed_cover_in_audio(audio_path: str, cover_path: str) -> bool:
    """Embed cover into audio file."""
    if not MUTAGEN_AVAILABLE:
        return False
    
    try:
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        audio = MutagenFile(audio_path)
        if audio is None:
            return False
        
        if isinstance(audio, MP4):
            audio.tags['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
            return True
        
        elif isinstance(audio, MP3):
            if audio.tags is None:
                audio.add_tags()
            audio.tags.delall('APIC')
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
            audio.save()
            return True
        
        elif isinstance(audio, FLAC):
            audio.clear_pictures()
            picture = Picture()
            picture.data = cover_data
            picture.type = 3
            picture.mime = 'image/jpeg'
            audio.add_picture(picture)
            audio.save()
            return True
        
        elif isinstance(audio, OggVorbis):
            picture = Picture()
            picture.data = cover_data
            picture.type = 3
            picture.mime = 'image/jpeg'
            picture_data = base64.b64encode(picture.write()).decode('ascii')
            audio['metadata_block_picture'] = picture_data
            audio.save()
            return True
        
        return False
        
    except Exception as e:
        return False


def process_audiobook(audiobook: Dict, image_url: str) -> bool:
    """Download and embed cover for audiobook."""
    author = audiobook['author']
    title = audiobook['title']
    path = audiobook['path']
    
    print(f"\n{'='*70}")
    print(f"Processing: {author} - {title}")
    print(f"{'='*70}")
    
    # Download cover
    cover_path = os.path.join(path, "cover.jpg")
    if not download_image(image_url, cover_path):
        return False
    
    print(f"  ✓ Saved to: {cover_path}")
    
    # Embed in audio files
    if MUTAGEN_AVAILABLE:
        audio_files = audiobook.get('audio_files', [])
        embedded_count = 0
        
        for audio_file in audio_files[:3]:  # First 3 files
            audio_path = os.path.join(path, audio_file)
            if embed_cover_in_audio(audio_path, cover_path):
                embedded_count += 1
        
        print(f"  ✓ Embedded in {embedded_count}/{min(3, len(audio_files))} audio files")
    
    return True


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          AUDIOBOOK COVER DOWNLOADER                                ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    missing = load_missing_audiobooks()
    print(f"Found {len(missing)} audiobooks missing covers\n")
    
    for i, audiobook in enumerate(missing, 1):
        print(f"\n[{i}/{len(missing)}] {audiobook['author']} - {audiobook['title']}")
    
    print(f"\n{'='*70}")
    print("This script will help you download covers for these audiobooks.")
    print("You'll need to provide the image URL for each audiobook.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

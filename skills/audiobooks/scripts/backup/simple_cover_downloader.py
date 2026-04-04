"""
Simple Cover Downloader - Uses direct image search
For manual use: Search for cover, provide URL, downloads and embeds
"""

import json
import os
import requests
import base64
from typing import Dict

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


def list_missing_audiobooks():
    """List all audiobooks missing covers."""
    with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing = [ab for ab in data['audiobooks'] 
               if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
    
    return missing


def download_and_embed(audiobook_index: int, image_url: str) -> bool:
    """Download cover and embed it for a specific audiobook."""
    missing = list_missing_audiobooks()
    
    if audiobook_index < 1 or audiobook_index > len(missing):
        print(f"✗ Invalid index. Must be between 1 and {len(missing)}")
        return False
    
    audiobook = missing[audiobook_index - 1]
    author = audiobook['author']
    title = audiobook['title']
    path = audiobook['path']
    
    print(f"\nProcessing: {author} - {title}")
    
    try:
        # Download
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Save as file
        cover_path = os.path.join(path, "cover.jpg")
        with open(cover_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ Downloaded: {len(response.content) / 1024:.1f} KB")
        print(f"  ✓ Saved to: {cover_path}")
        
        # Embed in audio files
        if MUTAGEN_AVAILABLE:
            audio_files = audiobook.get('audio_files', [])
            embedded = 0
            cover_data = response.content
            
            for audio_file in audio_files[:5]:  # First 5 files
                audio_path = os.path.join(path, audio_file)
                
                try:
                    audio = MutagenFile(audio_path)
                    if audio is None:
                        continue
                    
                    if isinstance(audio, MP4):
                        audio.tags['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
                        audio.save()
                        embedded += 1
                    elif isinstance(audio, MP3):
                        if audio.tags is None:
                            audio.add_tags()
                        audio.tags.delall('APIC')
                        audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
                        audio.save()
                        embedded += 1
                    elif isinstance(audio, FLAC):
                        audio.clear_pictures()
                        picture = Picture()
                        picture.data = cover_data
                        picture.type = 3
                        picture.mime = 'image/jpeg'
                        audio.add_picture(picture)
                        audio.save()
                        embedded += 1
                    elif isinstance(audio, OggVorbis):
                        picture = Picture()
                        picture.data = cover_data
                        picture.type = 3
                        picture.mime = 'image/jpeg'
                        picture_data = base64.b64encode(picture.write()).decode('ascii')
                        audio['metadata_block_picture'] = picture_data
                        audio.save()
                        embedded += 1
                except Exception as e:
                    continue
            
            print(f"  ✓ Embedded in {embedded} audio files")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║            SIMPLE COVER DOWNLOADER                                 ║
╚════════════════════════════════════════════════════════════════════╝

This tool downloads and embeds cover images for audiobooks.

USAGE:
  python simple_cover_downloader.py

Then follow the prompts to:
  1. See list of audiobooks missing covers
  2. Choose an audiobook by number
  3. Provide the cover image URL
  4. The cover will be downloaded and embedded automatically
    """)
    
    missing = list_missing_audiobooks()
    
    print(f"\nAUDIOBOOKS MISSING COVERS ({len(missing)} total):")
    print("="*70)
    
    for i, ab in enumerate(missing, 1):
        print(f"{i:2}. {ab['author']} - {ab['title']}")
    
    print("\n" + "="*70)
    print("\nTo download a cover:")
    print("  1. Search for the audiobook on Audible or Amazon")
    print("  2. Right-click the cover image and 'Copy image address'")
    print("  3. Run: python simple_cover_downloader.py <number> <url>")
    print("\nExample:")
    print('  python simple_cover_downloader.py 1 "https://m.media-amazon.com/images/I/51abc123.jpg"')


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        # Direct mode: audiobook number and URL provided
        try:
            index = int(sys.argv[1])
            url = sys.argv[2]
            download_and_embed(index, url)
        except ValueError:
            print("✗ Invalid audiobook number")
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        # Interactive mode: show list
        main()

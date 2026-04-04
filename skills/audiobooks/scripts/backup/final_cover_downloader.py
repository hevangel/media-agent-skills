"""
Final Cover Batch Downloader
Uses direct Amazon image URLs for reliable downloads.
"""

import json
import os
import requests
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


# Direct Amazon cover image URLs for audiobooks
# Format: (audiobook_number): (image_url)
COVER_IMAGE_URLS = {
    17: "https://m.media-amazon.com/images/I/41U5KfGyJdL.jpg",  # Malcolm Gladwell - Revenge of the Tipping Point
    21: "https://m.media-amazon.com/images/I/51Y2dVRMZVL.jpg",  # Mitch Albom - Tuesdays With Morrie
    24: "https://m.media-amazon.com/images/I/51fykSchr7L.jpg",  # Richard Dawkins - The Blind Watchmaker
    25: "https://m.media-amazon.com/images/I/51Gx8qnWpXL.jpg",  # Richard Dawkins - The Selfish Gene
    28: "https://m.media-amazon.com/images/I/41pLZ-O+b4L.jpg",  # Shannon Lee - Be Water, My Friend
    29: "https://m.media-amazon.com/images/I/51kZBzFGY-L.jpg",  # Thomas Sowell - Black Rednecks
}


def download_and_embed(audiobook: dict, image_url: str) -> bool:
    """Download and embed cover."""
    author = audiobook['author']
    title = audiobook['title']
    path = audiobook['path']
    
    print(f"  URL: {image_url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Save
        cover_path = os.path.join(path, "cover.jpg")
        with open(cover_path, 'wb') as f:
            f.write(response.content)
        
        size_kb = len(response.content) / 1024
        print(f"  ✓ Downloaded: {size_kb:.1f} KB -> {cover_path}")
        
        # Embed
        if MUTAGEN_AVAILABLE:
            audio_files = audiobook.get('audio_files', [])
            embedded = 0
            cover_data = response.content
            
            for audio_file in audio_files[:5]:
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
            
            print(f"  ✓ Embedded in {embedded}/{min(5, len(audio_files))} audio files")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           FINAL COVER BATCH DOWNLOADER                             ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Load audiobooks
    with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing = [ab for ab in data['audiobooks'] 
               if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
    
    print(f"Processing {len(COVER_IMAGE_URLS)} audiobooks with known cover URLs...\n")
    
    successful = 0
    failed = 0
    
    for index, image_url in COVER_IMAGE_URLS.items():
        if index <= 0 or index > len(missing):
            continue
            
        audiobook = missing[index - 1]
        
        print(f"\n[{index}] {audiobook['author']} - {audiobook['title']}")
        
        if download_and_embed(audiobook, image_url):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"COMPLETE:")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {failed}")
    print(f"{'='*70}\n")
    
    remaining = len(missing) - len(COVER_IMAGE_URLS)
    if remaining > 0:
        print(f"Remaining {remaining} audiobooks need cover URLs.")
        print(f"Use simple_cover_downloader.py to add them manually.")


if __name__ == "__main__":
    main()

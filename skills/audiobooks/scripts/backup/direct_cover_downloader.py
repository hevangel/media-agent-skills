"""
Simple Direct Cover Downloader
Provide direct image URLs to download and embed covers.
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


# Direct cover image URLs - update these with actual URLs from Google Images/Audible
COVER_URLS = {
    17: "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1714661696i/209254569.jpg",  # Revenge of the Tipping Point
    25: "https://m.media-amazon.com/images/I/81xpvlBk9FL._SY522_.jpg",  # The Selfish Gene
    29: "https://m.media-amazon.com/images/I/51PB6TYe-8L._SY445_SX342_.jpg",  # Black Rednecks
    21: "https://m.media-amazon.com/images/I/51RWE-FUqYL._SY445_SX342_.jpg",  # Tuesdays With Morrie
    3: "https://m.media-amazon.com/images/I/81mlWQ94rgL._SY522_.jpg",  # 2001 A Space Odyssey
}


def download_and_embed(audiobook_index, audiobook, image_url):
    """Download and embed cover."""
    author = audiobook['author']
    title = audiobook['title']
    path = audiobook['path']
    
    print(f"\n[{audiobook_index}] {author} - {title}")
    print(f"{'='*70}")
    
    try:
        # Download
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
            embedded = 0
            cover_data = response.content
            audio_files = audiobook.get('audio_files', [])
            
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
                except Exception:
                    continue
            
            print(f"  ✓ Embedded in {embedded} audio files")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          DIRECT COVER DOWNLOADER                                   ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Load audiobooks
    with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing = [ab for ab in data['audiobooks'] 
               if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
    
    print(f"Processing {len(COVER_URLS)} audiobooks with configured URLs...\n")
    
    successful = 0
    for index, url in COVER_URLS.items():
        if 1 <= index <= len(missing):
            if download_and_embed(index, missing[index-1], url):
                successful += 1
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {successful}/{len(COVER_URLS)} covers processed")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

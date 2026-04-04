"""Automated audiobook cover downloader using Playwright MCP browser.

This script processes audiobooks missing covers by:
1. Searching Audible for each book
2. Capturing the cover image
3. Embedding it in the audio files
"""

import json
import os
import shutil
import time
from pathlib import Path
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis

# Paths
SCAN_RESULTS = 'audiobook_scan_results.json'
PLAYWRIGHT_SCREENSHOTS = r'c:\Users\hevan\work\ai_agents\.playwright-mcp'
LOG_FILE = 'cover_download_log.json'

def load_missing_audiobooks():
    """Load list of audiobooks missing covers."""
    with open(SCAN_RESULTS, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing = [ab for ab in data['audiobooks'] 
               if not ab['has_cover'] and not ab['has_embedded_cover']]
    
    return missing

def build_audible_search_url(author, title):
    """Build Audible search URL for author and title."""
    import urllib.parse
    query = f"{author} {title}"
    encoded_query = urllib.parse.quote(query)
    return f"https://www.audible.com/search?keywords={encoded_query}"

def embed_cover_in_mp4(audio_file, cover_data):
    """Embed cover in MP4/M4A/M4B file."""
    try:
        audio = MP4(audio_file)
        # Detect image format from cover data
        if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
            format_type = MP4Cover.FORMAT_PNG
        else:
            format_type = MP4Cover.FORMAT_JPEG
        audio["covr"] = [MP4Cover(cover_data, imageformat=format_type)]
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in MP4: {e}")
        return False

def embed_cover_in_mp3(audio_file, cover_data):
    """Embed cover in MP3 file."""
    try:
        audio = MP3(audio_file, ID3=ID3)
        try:
            audio.tags
        except:
            audio.add_tags()
        
        audio.tags.delall("APIC")
        
        # Detect MIME type
        if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime = 'image/png'
        else:
            mime = 'image/jpeg'
        
        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime,
                type=3,
                desc='Cover',
                data=cover_data
            )
        )
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in MP3: {e}")
        return False

def embed_cover_in_flac(audio_file, cover_data):
    """Embed cover in FLAC file."""
    try:
        audio = FLAC(audio_file)
        audio.clear_pictures()
        
        picture = Picture()
        picture.type = 3
        if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
            picture.mime = 'image/png'
        else:
            picture.mime = 'image/jpeg'
        picture.desc = 'Cover'
        picture.data = cover_data
        
        audio.add_picture(picture)
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in FLAC: {e}")
        return False

def embed_cover_in_ogg(audio_file, cover_data):
    """Embed cover in OGG file."""
    try:
        audio = OggVorbis(audio_file)
        
        picture = Picture()
        picture.type = 3
        if cover_data[:8] == b'\x89PNG\r\n\x1a\n':
            picture.mime = 'image/png'
        else:
            picture.mime = 'image/jpeg'
        picture.desc = 'Cover'
        picture.data = cover_data
        
        audio.pop('metadata_block_picture', None)
        
        import base64
        audio['metadata_block_picture'] = [base64.b64encode(picture.write()).decode('ascii')]
        
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in OGG: {e}")
        return False

def embed_cover_in_audiobook(audiobook, cover_image_path):
    """Embed cover in audiobook files."""
    path = audiobook['path']
    
    # Read cover data
    with open(cover_image_path, 'rb') as f:
        cover_data = f.read()
    
    # Copy to audiobook directory
    cover_dest = os.path.join(path, 'cover.jpg')
    shutil.copy2(cover_image_path, cover_dest)
    print(f"  Copied cover to: {cover_dest}")
    
    # Find audio files
    audio_extensions = ['.m4a', '.m4b', '.mp3', '.flac', '.ogg']
    audio_files = []
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(root, file))
    
    audio_files.sort()
    
    # Embed in first 5 files
    embedded_count = 0
    for audio_file in audio_files[:5]:
        ext = os.path.splitext(audio_file)[1].lower()
        
        success = False
        if ext in ['.m4a', '.m4b']:
            success = embed_cover_in_mp4(audio_file, cover_data)
        elif ext == '.mp3':
            success = embed_cover_in_mp3(audio_file, cover_data)
        elif ext == '.flac':
            success = embed_cover_in_flac(audio_file, cover_data)
        elif ext == '.ogg':
            success = embed_cover_in_ogg(audio_file, cover_data)
        
        if success:
            embedded_count += 1
    
    return embedded_count

def save_log(log_data):
    """Save processing log."""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def load_log():
    """Load processing log."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed': [], 'failed': [], 'skipped': []}

def main():
    """Main processing loop."""
    print("="*80)
    print("AUTOMATED AUDIOBOOK COVER DOWNLOADER")
    print("="*80)
    print()
    
    # Load audiobooks
    missing = load_missing_audiobooks()
    print(f"Found {len(missing)} audiobooks missing covers")
    print()
    
    # Load log
    log = load_log()
    processed_titles = set(log.get('processed', []))
    
    print("INSTRUCTIONS:")
    print("1. I will generate Audible search URLs for each audiobook")
    print("2. Please use the Playwright MCP browser to:")
    print("   - Navigate to the URL")
    print("   - Find the correct audiobook on the search results")
    print("   - Navigate to its product page")
    print("   - Take a screenshot of the cover image")
    print("   - Save it with a descriptive filename")
    print("3. Then I will embed the cover in the audiobook files")
    print()
    print("="*80)
    print()
    
    # Process first 5 audiobooks not yet processed
    to_process = [ab for ab in missing 
                  if f"{ab['author']} - {ab['title']}" not in processed_titles][:5]
    
    for i, audiobook in enumerate(to_process, 1):
        author = audiobook['author']
        title = audiobook['title']
        full_title = f"{author} - {title}"
        
        print(f"\n{'='*80}")
        print(f"AUDIOBOOK {i}/{len(to_process)}: {full_title}")
        print(f"{'='*80}")
        print(f"Path: {audiobook['path']}")
        print()
        
        # Generate search URL
        search_url = build_audible_search_url(author, title)
        print(f"Audible Search URL:")
        print(search_url)
        print()
        print("Please use Playwright MCP browser to:")
        print("1. Navigate to the URL above")
        print("2. Find the correct audiobook")
        print("3. Navigate to its product page")
        print("4. Take a screenshot of the cover image")
        print()
        print("Then type the filename of the screenshot (or 'skip' to skip this book)")
        print()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total audiobooks missing covers: {len(missing)}")
    print(f"Already processed: {len(processed_titles)}")
    print(f"Remaining: {len(missing) - len(processed_titles)}")
    print()
    print("URLs generated for the next 5 audiobooks.")
    print("Please use the Playwright MCP browser to download covers,")
    print("then run the embedding script to process them.")

if __name__ == "__main__":
    main()

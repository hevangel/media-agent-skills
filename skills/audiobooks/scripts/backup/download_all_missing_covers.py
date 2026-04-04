"""Automated script to download all missing audiobook covers from Audible."""

import os
import json
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from PIL import Image

# Paths
SCAN_RESULTS_FILE = r"B:\ai_agents\audiobook_cover\audiobook_scan_results.json"
COVERS_DIR = r"B:\ai_agents\.playwright-covers"
LOG_FILE = r"B:\ai_agents\audiobook_cover\cover_download_log.txt"

# Create covers directory
os.makedirs(COVERS_DIR, exist_ok=True)

def log_message(message):
    """Log message to file and print to console."""
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{message}\n")

def load_missing_audiobooks():
    """Load audiobooks that are missing covers."""
    with open(SCAN_RESULTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing = []
    for book in data['audiobooks']:
        if not book['has_cover'] and not book['has_embedded_cover']:
            missing.append(book)
    
    return missing

def embed_cover_in_audio(audio_file, cover_data):
    """Embed cover in audio file based on its format."""
    ext = os.path.splitext(audio_file)[1].lower()
    
    try:
        if ext in ['.m4a', '.m4b']:
            audio = MP4(audio_file)
            audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
        elif ext == '.mp3':
            audio = MP3(audio_file, ID3=ID3)
            try:
                audio.tags
            except:
                audio.add_tags()
            audio.tags.delall("APIC")
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
            audio.save()
        elif ext == '.flac':
            audio = FLAC(audio_file)
            audio.clear_pictures()
            picture = Picture()
            picture.type = 3
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = cover_data
            audio.add_picture(picture)
            audio.save()
        elif ext == '.ogg':
            audio = OggVorbis(audio_file)
            picture = Picture()
            picture.type = 3
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = cover_data
            import base64
            audio.pop('metadata_block_picture', None)
            audio['metadata_block_picture'] = [base64.b64encode(picture.write()).decode('ascii')]
            audio.save()
        else:
            return False
        return True
    except Exception as e:
        log_message(f"  ✗ Error embedding cover: {e}")
        return False

def process_audiobook_cover(book, cover_png_path):
    """Process downloaded cover: convert to JPG, copy to folder, embed in files."""
    try:
        # Convert PNG to JPG
        cover_jpg_path = cover_png_path.replace('.png', '.jpg')
        img = Image.open(cover_png_path)
        rgb_img = img.convert('RGB')
        rgb_img.save(cover_jpg_path, 'JPEG', quality=95)
        
        # Read cover data
        with open(cover_jpg_path, 'rb') as f:
            cover_data = f.read()
        
        # Copy to audiobook directory
        dest_path = os.path.join(book['path'], 'cover.jpg')
        shutil.copy2(cover_jpg_path, dest_path)
        log_message(f"  ✓ Copied cover to: {dest_path}")
        
        # Find audio files
        audio_files = []
        for root, dirs, files in os.walk(book['path']):
            for file in files:
                if any(file.lower().endswith(ext) for ext in ['.m4a', '.m4b', '.mp3', '.flac', '.ogg']):
                    audio_files.append(os.path.join(root, file))
        
        audio_files.sort()
        
        # Embed in first 5 files
        embedded_count = 0
        for audio_file in audio_files[:5]:
            if embed_cover_in_audio(audio_file, cover_data):
                embedded_count += 1
        
        log_message(f"  ✓ Embedded cover in {embedded_count}/{min(len(audio_files), 5)} files")
        return True
        
    except Exception as e:
        log_message(f"  ✗ Error processing cover: {e}")
        return False

def download_cover_from_audible(book, browser):
    """Download cover from Audible for a specific book."""
    author = book['author']
    title = book['title']
    
    log_message(f"\n{'='*60}")
    log_message(f"Processing: {title} by {author}")
    log_message(f"Path: {book['path']}")
    
    try:
        page = browser.new_page()
        
        # Search for the audiobook
        search_query = f"{author} {title}"
        search_url = f"https://www.audible.com/search?keywords={search_query.replace(' ', '+')}"
        log_message(f"  → Searching Audible: {search_query}")
        
        page.goto(search_url, timeout=30000)
        time.sleep(3)
        
        # Click on first result
        try:
            first_result = page.locator('li.productListItem').first
            first_result.locator('a').first.click()
            time.sleep(3)
            log_message(f"  → Opened product page")
        except Exception as e:
            log_message(f"  ✗ Could not find search results: {e}")
            page.close()
            return False
        
        # Screenshot the cover image
        cover_filename = f"{author.replace(' ', '_').lower()}_{title.replace(' ', '_').lower()[:30]}_cover.png"
        cover_path = os.path.join(COVERS_DIR, cover_filename)
        
        try:
            cover_img = page.locator('img[alt*="Audiobook"]').first
            cover_img.screenshot(path=cover_path)
            log_message(f"  ✓ Downloaded cover screenshot")
        except Exception as e:
            log_message(f"  ✗ Could not screenshot cover: {e}")
            page.close()
            return False
        
        page.close()
        
        # Process the cover
        if os.path.exists(cover_path):
            return process_audiobook_cover(book, cover_path)
        else:
            log_message(f"  ✗ Cover file not found: {cover_path}")
            return False
            
    except Exception as e:
        log_message(f"  ✗ Error downloading cover: {e}")
        return False

def main():
    """Main function to process all missing covers."""
    log_message(f"\n{'='*60}")
    log_message(f"AUDIOBOOK COVER DOWNLOAD AUTOMATION")
    log_message(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"{'='*60}")
    
    # Load missing audiobooks
    missing_books = load_missing_audiobooks()
    log_message(f"\nFound {len(missing_books)} audiobooks without covers")
    
    # Skip Malcolm Gladwell (already processed)
    missing_books = [b for b in missing_books if 'Malcolm Gladwell' not in b['path']]
    missing_books = [b for b in missing_books if 'Dawkins' not in b['path']]  # Skip already done
    missing_books = [b for b in missing_books if 'Ben Shapiro' not in b['path']]  # Skip already done
    
    log_message(f"Processing {len(missing_books)} remaining audiobooks...\n")
    
    # Launch browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        success_count = 0
        fail_count = 0
        
        for i, book in enumerate(missing_books[:10], 1):  # Process 10 at a time
            log_message(f"\n[{i}/{min(len(missing_books), 10)}]")
            
            if download_cover_from_audible(book, browser):
                success_count += 1
            else:
                fail_count += 1
            
            # Small delay between books
            time.sleep(2)
        
        browser.close()
    
    log_message(f"\n{'='*60}")
    log_message(f"SUMMARY")
    log_message(f"{'='*60}")
    log_message(f"Successfully processed: {success_count} audiobooks")
    log_message(f"Failed: {fail_count} audiobooks")
    log_message(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

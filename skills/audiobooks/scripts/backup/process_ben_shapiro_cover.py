"""Process Ben Shapiro audiobook cover."""

import os
import shutil
from pathlib import Path
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

# Configuration
cover_image_path = r"c:\Users\hevan\work\ai_agents\.playwright-mcp\ben_shapiro_destroy_america_cover.png"
audiobook_path = r"E:\audiobooks\Ben Shapiro\How to Destroy America in Three Easy Steps"

def convert_png_to_jpg(png_path):
    """Convert PNG to JPG."""
    jpg_path = png_path.replace('.png', '.jpg')
    try:
        img = Image.open(png_path)
        rgb_img = img.convert('RGB')
        rgb_img.save(jpg_path, 'JPEG', quality=95)
        print(f"Converted to JPEG: {jpg_path}")
        return jpg_path
    except Exception as e:
        print(f"Error converting image: {e}")
        return None

def embed_cover_in_mp3(audio_file, cover_data):
    """Embed cover in MP3 file."""
    try:
        audio = MP3(audio_file, ID3=ID3)
        
        # Try to load existing ID3 tags
        try:
            audio.tags
        except:
            audio.add_tags()
        
        # Remove existing covers
        audio.tags.delall("APIC")
        
        # Add new cover
        audio.tags.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,  # Cover (front)
                desc='Cover',
                data=cover_data
            )
        )
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in MP3 {audio_file}: {e}")
        return False

def process_audiobook():
    """Process the audiobook."""
    
    if not os.path.exists(cover_image_path):
        print(f"Cover image not found: {cover_image_path}")
        return False
    
    if not os.path.exists(audiobook_path):
        print(f"Audiobook directory not found: {audiobook_path}")
        return False
    
    print(f"Processing: {audiobook_path}")
    
    # Convert PNG to JPG
    jpg_path = convert_png_to_jpg(cover_image_path)
    if not jpg_path:
        return False
    
    # Read cover data
    with open(jpg_path, 'rb') as f:
        cover_data = f.read()
    
    # Copy to audiobook directory
    cover_dest = os.path.join(audiobook_path, 'cover.jpg')
    shutil.copy2(jpg_path, cover_dest)
    print(f"Copied cover to: {cover_dest}")
    
    # Find MP3 files
    audio_files = []
    for root, dirs, files in os.walk(audiobook_path):
        for file in files:
            if file.lower().endswith('.mp3'):
                audio_files.append(os.path.join(root, file))
    
    audio_files.sort()
    
    # Embed in first 5 files
    embedded_count = 0
    for audio_file in audio_files[:5]:
        print(f"Embedding cover in: {os.path.basename(audio_file)}")
        if embed_cover_in_mp3(audio_file, cover_data):
            embedded_count += 1
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Failed")
    
    print(f"\nSummary:")
    print(f"- Total MP3 files: {len(audio_files)}")
    print(f"- Embedded in: {embedded_count} files")
    print(f"- Cover saved to: {cover_dest}")
    
    return True

if __name__ == "__main__":
    process_audiobook()

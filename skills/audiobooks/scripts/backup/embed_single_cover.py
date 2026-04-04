"""Embed cover image from Playwright screenshot into audiobook files."""

import os
import json
import shutil
from pathlib import Path
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis

# Configuration
cover_image_path = r"c:\Users\hevan\work\ai_agents\.playwright-mcp\revenge_of_tipping_point_cover.png"
audiobook_path = r"E:\audiobooks\Malcolm Gladwell\Revenge of the Tipping Point"

def embed_cover_in_mp4(audio_file, cover_data):
    """Embed cover in MP4/M4A/M4B file."""
    try:
        audio = MP4(audio_file)
        audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_PNG)]
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in MP4 {audio_file}: {e}")
        return False

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
                mime='image/png',
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

def embed_cover_in_flac(audio_file, cover_data):
    """Embed cover in FLAC file."""
    try:
        audio = FLAC(audio_file)
        
        # Remove existing pictures
        audio.clear_pictures()
        
        # Create picture
        picture = Picture()
        picture.type = 3  # Cover (front)
        picture.mime = 'image/png'
        picture.desc = 'Cover'
        picture.data = cover_data
        
        audio.add_picture(picture)
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in FLAC {audio_file}: {e}")
        return False

def embed_cover_in_ogg(audio_file, cover_data):
    """Embed cover in OGG file."""
    try:
        audio = OggVorbis(audio_file)
        
        # Create picture
        picture = Picture()
        picture.type = 3  # Cover (front)
        picture.mime = 'image/png'
        picture.desc = 'Cover'
        picture.data = cover_data
        
        # Remove existing covers
        audio.pop('metadata_block_picture', None)
        
        # Add new cover
        import base64
        audio['metadata_block_picture'] = [base64.b64encode(picture.write()).decode('ascii')]
        
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding in OGG {audio_file}: {e}")
        return False

def process_audiobook():
    """Process the audiobook: copy cover file and embed in audio files."""
    
    # Check if cover image exists
    if not os.path.exists(cover_image_path):
        print(f"Cover image not found: {cover_image_path}")
        return False
    
    # Check if audiobook directory exists
    if not os.path.exists(audiobook_path):
        print(f"Audiobook directory not found: {audiobook_path}")
        return False
    
    print(f"Processing audiobook: {audiobook_path}")
    
    # Read cover image data
    with open(cover_image_path, 'rb') as f:
        cover_data = f.read()
    
    # Copy cover.jpg to audiobook directory
    cover_dest = os.path.join(audiobook_path, 'cover.jpg')
    try:
        shutil.copy2(cover_image_path, cover_dest)
        print(f"Copied cover image to: {cover_dest}")
    except Exception as e:
        print(f"Error copying cover: {e}")
    
    # Find all audio files
    audio_extensions = ['.m4a', '.m4b', '.mp3', '.flac', '.ogg']
    audio_files = []
    
    for root, dirs, files in os.walk(audiobook_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(root, file))
    
    # Sort audio files
    audio_files.sort()
    
    # Embed cover in first 5 audio files
    embedded_count = 0
    for audio_file in audio_files[:5]:
        ext = os.path.splitext(audio_file)[1].lower()
        
        print(f"Embedding cover in: {os.path.basename(audio_file)}")
        
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
            print(f"  ✓ Successfully embedded cover")
        else:
            print(f"  ✗ Failed to embed cover")
    
    print(f"\nSummary:")
    print(f"- Total audio files found: {len(audio_files)}")
    print(f"- Cover embedded in: {embedded_count} files")
    print(f"- Cover file saved to: {cover_dest}")
    
    return True

if __name__ == "__main__":
    process_audiobook()

#!/usr/bin/env python3
"""Process Ben Shapiro - How to Destroy America in Three Easy Steps audiobook"""

from pathlib import Path
from PIL import Image
import io

# Import mutagen modules for different audio formats
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis

def detect_image_format(image_path):
    """Detect if image is PNG or JPEG and return appropriate format"""
    with Image.open(image_path) as img:
        if img.format == 'PNG':
            return 'PNG', img
        elif img.format in ['JPEG', 'JPG']:
            return 'JPEG', img
        else:
            # Convert to JPEG if unknown format
            return 'JPEG', img.convert('RGB')

def embed_cover_in_mp4(audio_file, cover_data):
    """Embed cover in MP4/M4A/M4B file"""
    audio = MP4(audio_file)
    audio['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
    audio.save()

def embed_cover_in_mp3(audio_file, cover_data):
    """Embed cover in MP3 file"""
    audio = MP3(audio_file, ID3=ID3)
    
    # Add ID3 tag if it doesn't exist
    try:
        audio.add_tags()
    except:
        pass
    
    # Remove existing covers
    audio.tags.delall('APIC')
    
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

def embed_cover_in_flac(audio_file, cover_data):
    """Embed cover in FLAC file"""
    audio = FLAC(audio_file)
    
    # Clear existing pictures
    audio.clear_pictures()
    
    # Create picture
    picture = Picture()
    picture.type = 3  # Cover (front)
    picture.mime = 'image/jpeg'
    picture.desc = 'Cover'
    picture.data = cover_data
    
    audio.add_picture(picture)
    audio.save()

def embed_cover_in_ogg(audio_file, cover_data):
    """Embed cover in OGG Vorbis file"""
    audio = OggVorbis(audio_file)
    
    # Clear existing pictures
    audio.clear_pictures()
    
    # Create picture
    picture = Picture()
    picture.type = 3  # Cover (front)
    picture.mime = 'image/jpeg'
    picture.desc = 'Cover'
    picture.data = cover_data
    
    audio.add_picture(picture)
    audio.save()

def process_audiobook():
    """Process the audiobook: convert cover and embed in audio files"""
    
    # Paths
    audiobook_dir = Path(r"E:\audiobooks\Ben Shapiro\How to Destroy America in Three Easy Steps")
    downloaded_cover = Path(r"c:\Users\hevan\work\ai_agents\.playwright-mcp\ben_shapiro_destroy_america_cover.png")
    cover_dest = audiobook_dir / "cover.jpg"
    
    print("=" * 80)
    print("PROCESSING: How to Destroy America in Three Easy Steps by Ben Shapiro")
    print("=" * 80)
    print()
    print(f"Audiobook directory: {audiobook_dir}")
    print(f"Downloaded cover: {downloaded_cover}")
    print()
    
    # Convert PNG to JPEG and copy to audiobook directory
    print(f"Converting and copying cover to: {cover_dest}")
    img_format, img = detect_image_format(downloaded_cover)
    
    if img_format == 'PNG':
        # Convert PNG to RGB (remove alpha channel) then save as JPEG
        rgb_img = img.convert('RGB')
        rgb_img.save(cover_dest, 'JPEG', quality=95)
    else:
        # Already JPEG, just copy
        img.save(cover_dest, 'JPEG', quality=95)
    
    print(f"✓ Cover saved as: {cover_dest}")
    print()
    
    # Load cover data for embedding
    with open(cover_dest, 'rb') as f:
        cover_data = f.read()
    
    # Find all audio files
    audio_extensions = ('.mp3', '.m4a', '.m4b', '.flac', '.ogg')
    audio_files = sorted([f for f in audiobook_dir.iterdir() if f.suffix.lower() in audio_extensions])
    
    print(f"Found {len(audio_files)} audio file(s)")
    print()
    
    # Embed cover in first 5 files (or all if less than 5)
    files_to_process = audio_files[:5]
    print(f"Embedding cover in {len(files_to_process)} file(s):")
    print()
    
    successful = 0
    for audio_file in files_to_process:
        try:
            ext = audio_file.suffix.lower()
            
            if ext in ['.m4a', '.m4b']:
                embed_cover_in_mp4(str(audio_file), cover_data)
            elif ext == '.mp3':
                embed_cover_in_mp3(str(audio_file), cover_data)
            elif ext == '.flac':
                embed_cover_in_flac(str(audio_file), cover_data)
            elif ext == '.ogg':
                embed_cover_in_ogg(str(audio_file), cover_data)
            
            print(f"  ✓ Embedded cover in: {audio_file.name}")
            successful += 1
        except Exception as e:
            print(f"  ✗ Failed to embed in {audio_file.name}: {e}")
    
    print()
    print("=" * 80)
    print(f"SUMMARY: Embedded cover in {successful}/{len(files_to_process)} file(s)")
    print("=" * 80)

if __name__ == "__main__":
    process_audiobook()

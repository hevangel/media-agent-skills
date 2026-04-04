import json
import shutil
from pathlib import Path
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from PIL import Image
import io

def detect_image_format(image_path):
    """Detect if image is PNG or JPEG"""
    try:
        with Image.open(image_path) as img:
            return img.format.upper()
    except Exception as e:
        print(f"Error detecting image format: {e}")
        return None

def embed_cover_in_mp4(audio_file, cover_path):
    """Embed cover art in MP4/M4A/M4B file"""
    try:
        audio = MP4(audio_file)
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        # Detect image format
        img_format = detect_image_format(cover_path)
        if img_format == 'PNG':
            image_format = MP4Cover.FORMAT_PNG
        else:
            image_format = MP4Cover.FORMAT_JPEG
        
        audio['covr'] = [MP4Cover(cover_data, imageformat=image_format)]
        audio.save()
        print(f"  ✓ Embedded cover in: {audio_file.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error embedding in {audio_file.name}: {e}")
        return False

def embed_cover_in_mp3(audio_file, cover_path):
    """Embed cover art in MP3 file"""
    try:
        audio = MP3(audio_file, ID3=ID3)
        
        # Add ID3 tag if it doesn't exist
        try:
            audio.add_tags()
        except:
            pass
        
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        # Detect image format
        img_format = detect_image_format(cover_path)
        mime_type = 'image/png' if img_format == 'PNG' else 'image/jpeg'
        
        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime_type,
                type=3,  # Cover (front)
                desc='Cover',
                data=cover_data
            )
        )
        audio.save()
        print(f"  ✓ Embedded cover in: {audio_file.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error embedding in {audio_file.name}: {e}")
        return False

def embed_cover_in_flac(audio_file, cover_path):
    """Embed cover art in FLAC file"""
    try:
        audio = FLAC(audio_file)
        
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        # Detect image format
        img_format = detect_image_format(cover_path)
        mime_type = 'image/png' if img_format == 'PNG' else 'image/jpeg'
        
        picture = Picture()
        picture.type = 3  # Cover (front)
        picture.mime = mime_type
        picture.desc = 'Cover'
        picture.data = cover_data
        
        audio.clear_pictures()
        audio.add_picture(picture)
        audio.save()
        print(f"  ✓ Embedded cover in: {audio_file.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error embedding in {audio_file.name}: {e}")
        return False

def embed_cover_in_ogg(audio_file, cover_path):
    """Embed cover art in OGG file"""
    try:
        audio = OggVorbis(audio_file)
        
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        # Detect image format
        img_format = detect_image_format(cover_path)
        mime_type = 'image/png' if img_format == 'PNG' else 'image/jpeg'
        
        picture = Picture()
        picture.type = 3  # Cover (front)
        picture.mime = mime_type
        picture.desc = 'Cover'
        picture.data = cover_data
        
        # Encode picture to base64 and add to metadata
        picture_data = picture.write()
        import base64
        encoded_data = base64.b64encode(picture_data).decode('ascii')
        audio['metadata_block_picture'] = [encoded_data]
        
        audio.save()
        print(f"  ✓ Embedded cover in: {audio_file.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error embedding in {audio_file.name}: {e}")
        return False

def process_audiobook():
    """Process The Blind Watchmaker audiobook"""
    
    # Paths
    audiobook_dir = Path(r"E:\audiobooks\Richard Dawkins\The Blind Watchmaker")
    downloaded_cover = Path(r"c:\Users\hevan\work\ai_agents\.playwright-mcp\blind_watchmaker_cover.png")
    target_cover = audiobook_dir / "cover.jpg"
    
    print(f"\n{'='*80}")
    print("PROCESSING: The Blind Watchmaker by Richard Dawkins")
    print(f"{'='*80}\n")
    
    # Check if audiobook directory exists
    if not audiobook_dir.exists():
        print(f"✗ Audiobook directory not found: {audiobook_dir}")
        return False
    
    # Check if downloaded cover exists
    if not downloaded_cover.exists():
        print(f"✗ Downloaded cover not found: {downloaded_cover}")
        return False
    
    print(f"Audiobook directory: {audiobook_dir}")
    print(f"Downloaded cover: {downloaded_cover}")
    
    # Convert PNG to JPEG and copy to audiobook directory
    try:
        print(f"\nConverting and copying cover to: {target_cover}")
        with Image.open(downloaded_cover) as img:
            # Convert to RGB if necessary (PNG might have alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                rgb_img.save(target_cover, 'JPEG', quality=95)
            else:
                img.save(target_cover, 'JPEG', quality=95)
        print(f"✓ Cover saved as: {target_cover}")
    except Exception as e:
        print(f"✗ Error copying cover: {e}")
        return False
    
    # Find audio files
    audio_extensions = {'.m4a', '.m4b', '.mp3', '.flac', '.ogg'}
    audio_files = [f for f in audiobook_dir.iterdir() if f.suffix.lower() in audio_extensions]
    
    if not audio_files:
        print(f"\n✗ No audio files found in: {audiobook_dir}")
        return False
    
    print(f"\nFound {len(audio_files)} audio file(s)")
    
    # Embed cover in audio files (first 5 or all if less than 5)
    files_to_process = sorted(audio_files)[:5]
    print(f"\nEmbedding cover in {len(files_to_process)} file(s):\n")
    
    success_count = 0
    for audio_file in files_to_process:
        ext = audio_file.suffix.lower()
        
        if ext in ['.m4a', '.m4b']:
            if embed_cover_in_mp4(audio_file, target_cover):
                success_count += 1
        elif ext == '.mp3':
            if embed_cover_in_mp3(audio_file, target_cover):
                success_count += 1
        elif ext == '.flac':
            if embed_cover_in_flac(audio_file, target_cover):
                success_count += 1
        elif ext == '.ogg':
            if embed_cover_in_ogg(audio_file, target_cover):
                success_count += 1
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: Embedded cover in {success_count}/{len(files_to_process)} file(s)")
    print(f"{'='*80}\n")
    
    return success_count > 0

if __name__ == "__main__":
    process_audiobook()

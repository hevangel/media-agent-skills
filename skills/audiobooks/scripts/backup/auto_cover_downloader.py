"""
Automated Cover Downloader
Searches Audible and downloads covers automatically.
"""

import json
import os
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import base64
import time

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


class CoverDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.results = []
        
    def extract_audible_cover_url(self, html: str) -> Optional[str]:
        """Extract cover image URL from Audible HTML."""
        # Look for common Audible cover image patterns
        patterns = [
            r'<img[^>]*src="(https://[^"]*m\.media-amazon\.com[^"]*\.jpg)"[^>]*cover',
            r'"image":"(https://[^"]*\.jpg)"',
            r'<meta property="og:image" content="([^"]*)"',
            r'data-image="([^"]*\.jpg)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                # Clean up the URL and get the largest version
                url = matches[0]
                # Convert to higher resolution
                url = re.sub(r'\._[^.]*_', '._SL500_', url)
                return url
        
        return None
    
    def search_and_get_cover_url(self, author: str, title: str) -> Optional[str]:
        """Search for audiobook and return cover URL."""
        try:
            # Clean up search terms
            author_clean = re.sub(r'[^\w\s]', '', author).strip()
            title_clean = re.sub(r'[^\w\s]', '', title).strip()
            
            #Search Google Images for high-res cover
            search_url = f"https://www.google.com/search?q={author_clean}+{title_clean}+audiobook+cover+site:audible.com&tbm=isch"
            
            print(f"  Searching for: {author} - {title}")
            
            # Alternative: Use Amazon product images
            # Most Audible books have Amazon pages too
            amazon_search = f"https://www.amazon.com/s?k={author_clean}+{title_clean}+audiobook"
            
            response = self.session.get(amazon_search, timeout=10)
            if response.status_code == 200:
                # Try to find image URLs in Amazon results
                img_pattern = r'https://m\.media-amazon\.com/images/I/[A-Z0-9+]+\._[^"]*\.jpg'
                matches = re.findall(img_pattern, response.text)
                
                if matches:
                    # Get the first high-res match
                    for match in matches:
                        if 'SL' in match or 'AC' in match:
                            # Convert to high resolution
                            url = re.sub(r'\._[^.]*_', '._SL500_', match)
                            print(f"  Found: {url[:80]}...")
                            return url
            
            return None
            
        except Exception as e:
            print(f"  Error searching: {e}")
            return None
    
    def download_image(self, url: str, save_path: str) -> bool:
        """Download image from URL."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            print(f"  ✓ Downloaded: {size_kb:.1f} KB")
            return True
            
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            return False
    
    def embed_cover(self, audio_path: str, cover_path: str) -> bool:
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
            elif isinstance(audio, MP3):
                if audio.tags is None:
                    audio.add_tags()
                audio.tags.delall('APIC')
                audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
                audio.save()
            elif isinstance(audio, FLAC):
                audio.clear_pictures()
                picture = Picture()
                picture.data = cover_data
                picture.type = 3
                picture.mime = 'image/jpeg'
                audio.add_picture(picture)
                audio.save()
            elif isinstance(audio, OggVorbis):
                picture = Picture()
                picture.data = cover_data
                picture.type = 3
                picture.mime = 'image/jpeg'
                picture_data = base64.b64encode(picture.write()).decode('ascii')
                audio['metadata_block_picture'] = picture_data
                audio.save()
            else:
                return False
                
            return True
            
        except Exception as e:
            return False
    
    def process_audiobook(self, audiobook: Dict) -> bool:
        """Process a single audiobook."""
        author = audiobook['author']
        title = audiobook['title']
        path = audiobook['path']
        
        print(f"\n{'='*70}")
        print(f"[{author}] {title}")
        print(f"{'='*70}")
        
        # Search for cover
        cover_url = self.search_and_get_cover_url(author, title)
        
        if not cover_url:
            print(f"  ✗ No cover found")
            self.results.append({'author': author, 'title': title, 'success': False})
            return False
        
        # Download cover
        cover_path = os.path.join(path, "cover.jpg")
        if not self.download_image(cover_url, cover_path):
            self.results.append({'author': author, 'title': title, 'success': False})
            return False
        
        # Embed in audio files
        if MUTAGEN_AVAILABLE:
            audio_files = audiobook.get('audio_files', [])
            embedded = 0
            
            for audio_file in audio_files[:3]:  # First 3 files
                audio_path = os.path.join(path, audio_file)
                if self.embed_cover(audio_path, cover_path):
                    embedded += 1
            
            print(f"  ✓ Embedded in {embedded} audio files")
        
        self.results.append({'author': author, 'title': title, 'success': True, 'url': cover_url})
        return True
    
    def run(self, limit: Optional[int] = None):
        """Run the downloader."""
        with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        missing = [ab for ab in data['audiobooks'] 
                   if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
        
        if limit:
            missing = missing[:limit]
        
        print(f"\nProcessing {len(missing)} audiobooks...")
        
        for i, audiobook in enumerate(missing, 1):
            print(f"\n[{i}/{len(missing)}]", end=" ")
            self.process_audiobook(audiobook)
            time.sleep(2)  # Be polite to servers
        
        # Save results
        with open("cover_download_results.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        successful = sum(1 for r in self.results if r.get('success'))
        print(f"\n{'='*70}")
        print(f"COMPLETE: {successful}/{len(self.results)} covers downloaded")
        print(f"{'='*70}")


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║       AUTOMATED AUDIOBOOK COVER DOWNLOADER                         ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    downloader = CoverDownloader()
    
    # Process first 10 as a test
    print("Processing first 10 audiobooks...")
    downloader.run(limit=10)


if __name__ == "__main__":
    main()

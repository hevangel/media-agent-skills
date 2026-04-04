"""
Audible Cover Downloader using DuckDuckGo Search
Searches for audiobooks on Audible/Amazon and downloads covers.
"""

import json
import os
import re
import requests
import time
import base64
from typing import Dict, Optional, Tuple

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


class AudibleCoverDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.results = []
    
    def search_audible_via_duckduckgo(self, author: str, title: str) -> Optional[str]:
        """Search for audiobook on Audible using DuckDuckGo."""
        # This will be called via MCP
        search_query = f'"{author}" "{title}" audiobook site:audible.com OR site:amazon.com'
        print(f"  Search: {search_query}")
        return search_query
    
    def extract_cover_from_audible_page(self, url: str) -> Optional[str]:
        """Extract cover image URL from Audible/Amazon page."""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            html = response.text
            
            # Try multiple patterns to find cover images
            patterns = [
                # Audible specific patterns
                r'"image":"(https://[^"]*m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
                r'<img[^>]*src="(https://[^"]*m\.media-amazon\.com/images/I/[^"]+\.jpg)"[^>]*product',
                r'<img[^>]*class="[^"]*bc-pub-block[^"]*"[^>]*src="(https://[^"]+\.jpg)"',
                r'<meta property="og:image" content="(https://[^"]*m\.media-amazon\.com/images/I/[^"]+\.jpg)"',
                # Amazon specific patterns
                r'data-a-dynamic-image="\{&quot;(https://m\.media-amazon\.com/images/I/[^&]+\.jpg)',
                r'"largeImage":"(https://[^"]*\.jpg)"',
                r'<img[^>]*id="landingImage"[^>]*src="(https://[^"]+\.jpg)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    url = matches[0]
                    # Ensure high resolution
                    url = re.sub(r'\._[A-Z0-9_,]+_\.', '._SL500_.', url)
                    # Remove any URL encoding
                    url = url.replace('&quot;', '').split('"')[0]
                    return url
            
            # Fallback: look for any media-amazon image
            all_images = re.findall(r'https://m\.media-amazon\.com/images/I/[A-Za-z0-9+]+\.jpg', html)
            if all_images:
                # Return the first one with decent size indicator
                for img in all_images:
                    if 'SL' in img or len(img) > 50:  # Likely a cover
                        return re.sub(r'\._[A-Z0-9_,]+_\.', '._SL500_.', img)
                return all_images[0]
            
            return None
            
        except Exception as e:
            print(f"  Error extracting cover: {str(e)[:100]}")
            return None
    
    def download_image(self, url: str, save_path: str) -> bool:
        """Download image from URL."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Verify it's an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type.lower():
                print(f"  ✗ Not an image: {content_type}")
                return False
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            print(f"  ✓ Downloaded: {size_kb:.1f} KB")
            return True
            
        except Exception as e:
            print(f"  ✗ Download failed: {str(e)[:100]}")
            return False
    
    def embed_cover_in_audio(self, audio_path: str, cover_path: str) -> bool:
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
    
    def process_audiobook_with_url(self, audiobook: Dict, audible_url: str) -> bool:
        """Process audiobook given its Audible URL."""
        author = audiobook['author']
        title = audiobook['title']
        path = audiobook['path']
        
        print(f"\n{'='*70}")
        print(f"{author} - {title}")
        print(f"{'='*70}")
        print(f"  URL: {audible_url}")
        
        # Extract cover URL from page
        cover_url = self.extract_cover_from_audible_page(audible_url)
        
        if not cover_url:
            print(f"  ✗ Could not extract cover from page")
            self.results.append({
                'author': author,
                'title': title,
                'success': False,
                'error': 'No cover found on page'
            })
            return False
        
        print(f"  Cover URL: {cover_url[:80]}...")
        
        # Download cover
        cover_path = os.path.join(path, "cover.jpg")
        if not self.download_image(cover_url, cover_path):
            self.results.append({
                'author': author,
                'title': title,
                'success': False,
                'error': 'Download failed'
            })
            return False
        
        # Embed in audio files
        embedded_count = 0
        if MUTAGEN_AVAILABLE:
            audio_files = audiobook.get('audio_files', [])
            for audio_file in audio_files[:5]:  # First 5 files
                audio_path = os.path.join(path, audio_file)
                if self.embed_cover_in_audio(audio_path, cover_path):
                    embedded_count += 1
        
        print(f"  ✓ Embedded in {embedded_count} audio files")
        
        self.results.append({
            'author': author,
            'title': title,
            'success': True,
            'cover_url': cover_url,
            'embedded_count': embedded_count
        })
        
        return True
    
    def save_results(self):
        """Save results to JSON."""
        with open("audible_cover_results.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        successful = sum(1 for r in self.results if r.get('success'))
        print(f"\n{'='*70}")
        print(f"RESULTS: {successful}/{len(self.results)} covers downloaded")
        print(f"Results saved to: audible_cover_results.json")
        print(f"{'='*70}")


def load_missing_audiobooks():
    """Load audiobooks missing covers."""
    with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return [ab for ab in data['audiobooks'] 
            if not ab.get('has_cover') and not ab.get('has_embedded_cover')]


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║     AUDIBLE COVER DOWNLOADER (via DuckDuckGo Search)              ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    missing = load_missing_audiobooks()
    print(f"Found {len(missing)} audiobooks missing covers\n")
    
    # Show list
    for i, ab in enumerate(missing, 1):
        print(f"{i:2}. {ab['author']} - {ab['title']}")
    
    print(f"\n{'='*70}")
    print("To process an audiobook, provide its Audible URL")
    print("Example: python audible_cover_downloader.py <audiobook_number> <audible_url>")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        # Process specific audiobook
        try:
            index = int(sys.argv[1]) - 1
            audible_url = sys.argv[2]
            
            missing = load_missing_audiobooks()
            if 0 <= index < len(missing):
                downloader = AudibleCoverDownloader()
                downloader.process_audiobook_with_url(missing[index], audible_url)
                downloader.save_results()
            else:
                print(f"Invalid index. Choose 1-{len(missing)}")
        except ValueError:
            print("Invalid index number")
    else:
        main()

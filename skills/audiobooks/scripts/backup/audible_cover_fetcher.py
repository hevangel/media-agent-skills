"""
Audible Cover Fetcher
Fetches cover images directly from Audible pages.
"""

import json
import os
import re
import requests
from typing import Dict, Optional, Tuple
import time
import base64
from urllib.parse import quote_plus

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


class AudibleCoverFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.results = []
        
    def search_audible(self, author: str, title: str) -> Optional[str]:
        """Search Audible and return the product page URL."""
        try:
            # Clean search terms - remove leading numbers from title
            title_clean = re.sub(r'^\d+\s+', '', title)
            search_query = f"{author} {title_clean} audiobook site:audible.com"
            
            print(f"  Searching: {author} - {title_clean[:40]}...")
            
            # Use DuckDuckGo search to find Audible page
            from urllib.parse import quote
            search_url = f"https://duckduckgo.com/html/?q={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            # Look for Audible product page links
            pattern = r'uddg=https%3A%2F%2Fwww\.audible\.com%2Fpd%2F([^&]+)'
            matches = re.findall(pattern, response.text)
            
            if matches:
                from urllib.parse import unquote
                product_path = unquote(matches[0])
                product_url = f"https://www.audible.com/pd/{product_path}"
                print(f"  Found: {product_url[:70]}...")
                return product_url
            
            # Fallback: direct Audible search
            encoded_query = quote_plus(f"{author} {title_clean}")
            search_url = f"https://www.audible.com/search?keywords={encoded_query}"
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            # Simple pattern to find first product link
            pattern = r'productListLink.*?href="(/pd/[^"]+)"'
            matches = re.findall(pattern, response.text)
            
            if matches:
                product_url = f"https://www.audible.com{matches[0]}"
                print(f"  Found: {product_url[:70]}...")
                return product_url
            
            return None
            
        except Exception as e:
            print(f"  Error: {str(e)[:60]}")
            return None
    
    def extract_cover_from_audible_page(self, url: str) -> Optional[str]:
        """Extract cover image URL from Audible product page."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            html = response.text
            
            # Multiple patterns to find cover images
            patterns = [
                # OpenGraph image
                r'<meta property="og:image" content="([^"]+)"',
                # Product image
                r'"image"\s*:\s*"([^"]+\.jpg)"',
                # Image srcset
                r'srcset="([^"]+\.jpg)',
                # Data image
                r'data-lazy="([^"]+\.jpg)"',
                # BC image container
                r'<img[^>]+class="[^"]*bc-image-inset-border[^"]*"[^>]+src="([^"]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    url = matches[0]
                    # Clean up and ensure high resolution
                    url = url.split('?')[0]  # Remove query params
                    # Try to get larger version
                    url = re.sub(r'\._[A-Z]{2}\d+_', '._SL500_', url)
                    if not url.startswith('http'):
                        continue
                    print(f"  Found image: {url[:70]}...")
                    return url
            
            return None
            
        except Exception as e:
            print(f"  Error extracting cover: {str(e)[:80]}")
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
            print(f"  ✗ Download failed: {str(e)[:80]}")
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
        """Process a single audiobook - search, download, embed."""
        author = audiobook['author']
        title = audiobook['title']
        path = audiobook['path']
        
        print(f"\n{'='*70}")
        print(f"[{author}] {title}")
        print(f"{'='*70}")
        
        # Search for product page
        product_url = self.search_audible(author, title)
        if not product_url:
            print(f"  ✗ Not found on Audible")
            self.results.append({
                'author': author,
                'title': title,
                'success': False,
                'error': 'Not found'
            })
            return False
        
        # Extract cover URL
        cover_url = self.extract_cover_from_audible_page(product_url)
        if not cover_url:
            print(f"  ✗ Could not extract cover image")
            self.results.append({
                'author': author,
                'title': title,
                'success': False,
                'error': 'No cover image'
            })
            return False
        
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
                if self.embed_cover(audio_path, cover_path):
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
    
    def run(self, limit: Optional[int] = None, skip: int = 0):
        """Run the fetcher."""
        # Load missing audiobooks
        with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        missing = [ab for ab in data['audiobooks'] 
                   if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
        
        if skip:
            missing = missing[skip:]
        
        if limit:
            missing = missing[:limit]
        
        print(f"\nProcessing {len(missing)} audiobooks...")
        if skip:
            print(f"(Starting from audiobook #{skip + 1})")
        
        for i, audiobook in enumerate(missing, 1):
            print(f"\n[{i}/{len(missing)}]", end=" ")
            self.process_audiobook(audiobook)
            
            # Be polite to Audible servers
            time.sleep(3)
        
        # Save results
        with open("audible_cover_results.json", 'w', encoding='utf-8') as f:
            json.dump({
                'total_processed': len(self.results),
                'successful': sum(1 for r in self.results if r.get('success')),
                'failed': sum(1 for r in self.results if not r.get('success')),
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        successful = sum(1 for r in self.results if r.get('success'))
        failed = len(self.results) - successful
        
        print(f"\n{'='*70}")
        print(f"COMPLETE:")
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Failed: {failed}")
        print(f"  Total: {len(self.results)}")
        print(f"{'='*70}")
        
        return self.results


def main():
    import sys
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║            AUDIBLE COVER FETCHER                                   ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    limit = None
    skip = 0
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            skip = int(sys.argv[2])
        except:
            pass
    
    fetcher = AudibleCoverFetcher()
    
    if limit:
        print(f"Processing first {limit} audiobooks...")
    else:
        print(f"Processing ALL missing audiobooks...")
    
    fetcher.run(limit=limit, skip=skip)


if __name__ == "__main__":
    main()

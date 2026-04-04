"""
Playwright Cover Downloader
Uses browser automation to download audiobook covers from Audible/Amazon.
"""

import json
import os
import time
import base64
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available. Install with: uv add playwright")
    print("Then run: playwright install chromium")

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


class PlaywrightCoverDownloader:
    def __init__(self):
        self.results = []
    
    def embed_cover_in_audio(self, audio_path: str, cover_data: bytes) -> bool:
        """Embed cover into audio file."""
        if not MUTAGEN_AVAILABLE:
            return False
        
        try:
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
        except Exception:
            return False
    
    def download_cover_from_audible(self, page, url: str) -> bytes:
        """Download cover from Audible page."""
        try:
            print(f"  Loading page...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(2)
            
            # Try multiple selectors for the cover image
            selectors = [
                'img.bc-pub-block',
                'img.bc-image-inset-border',
                'div.bc-image-wrapper img',
                'img[alt*="cover"]',
                'img[alt*="Cover"]',
            ]
            
            cover_img = None
            for selector in selectors:
                try:
                    cover_img = page.locator(selector).first
                    if cover_img.is_visible():
                        break
                except:
                    continue
            
            if not cover_img:
                print(f"  ✗ Could not find cover image on page")
                return None
            
            # Get the image source
            img_src = cover_img.get_attribute('src')
            if not img_src:
                print(f"  ✗ No image source found")
                return None
            
            print(f"  Found image: {img_src[:80]}...")
            
            # Convert to high resolution
            if '_' in img_src:
                img_src = img_src.split('._')[0] + '._SL500_.jpg'
            
            # Download the image using browser
            response = page.request.get(img_src)
            if response.ok:
                return response.body()
            else:
                print(f"  ✗ Failed to download image: {response.status}")
                return None
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            return None
    
    def process_audiobook(self, browser, audiobook: dict, url: str) -> bool:
        """Process a single audiobook."""
        author = audiobook['author']
        title = audiobook['title']
        path = audiobook['path']
        
        print(f"\n{'='*70}")
        print(f"{author} - {title}")
        print(f"{'='*70}")
        print(f"  URL: {url}")
        
        # Create new page
        page = browser.new_page()
        
        try:
            # Download cover
            cover_data = self.download_cover_from_audible(page, url)
            
            if not cover_data:
                self.results.append({
                    'author': author,
                    'title': title,
                    'success': False,
                    'error': 'Failed to download'
                })
                return False
            
            # Save to file
            cover_path = os.path.join(path, "cover.jpg")
            with open(cover_path, 'wb') as f:
                f.write(cover_data)
            
            size_kb = len(cover_data) / 1024
            print(f"  ✓ Downloaded: {size_kb:.1f} KB -> {cover_path}")
            
            # Embed in audio files
            embedded_count = 0
            if MUTAGEN_AVAILABLE:
                audio_files = audiobook.get('audio_files', [])
                for audio_file in audio_files[:5]:  # First 5 files
                    audio_path = os.path.join(path, audio_file)
                    if self.embed_cover_in_audio(audio_path, cover_data):
                        embedded_count += 1
                
                print(f"  ✓ Embedded in {embedded_count} audio files")
            
            self.results.append({
                'author': author,
                'title': title,
                'success': True,
                'embedded_count': embedded_count
            })
            
            return True
            
        finally:
            page.close()
    
    def run(self, audiobook_urls: dict):
        """Run the downloader with provided URLs."""
        if not PLAYWRIGHT_AVAILABLE:
            print("ERROR: Playwright not installed!")
            return
        
        print("Starting browser...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            try:
                for index, url in audiobook_urls.items():
                    with open("audiobook_scan_results.json", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    missing = [ab for ab in data['audiobooks'] 
                               if not ab.get('has_cover') and not ab.get('has_embedded_cover')]
                    
                    if 1 <= index <= len(missing):
                        self.process_audiobook(browser, missing[index-1], url)
                        time.sleep(2)  # Be polite
                
            finally:
                browser.close()
        
        # Save results
        with open("playwright_cover_results.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        successful = sum(1 for r in self.results if r.get('success'))
        print(f"\n{'='*70}")
        print(f"COMPLETE: {successful}/{len(self.results)} covers downloaded")
        print(f"Results saved to: playwright_cover_results.json")
        print(f"{'='*70}")


def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║     PLAYWRIGHT COVER DOWNLOADER                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    if not PLAYWRIGHT_AVAILABLE:
        print("\nPlaywright not installed!")
        print("Install with:")
        print("  uv add playwright")
        print("  playwright install chromium")
        return
    
    # URLs to process (audiobook index -> Audible/Amazon URL)
    AUDIOBOOK_URLS = {
        17: "https://www.audible.com/pd/Revenge-of-the-Tipping-Point-Audiobook/B0D5R9GG1D",
        25: "https://www.audible.com/pd/The-Selfish-Gene-Audiobook/B004QDTA9Y",
        29: "https://www.audible.com/pd/Black-Rednecks-and-White-Liberals-Audiobook/B002V8HBWO",
        21: "https://www.audible.com/pd/Tuesdays-with-Morrie-Audiobook/B002V0KXWY",
        3: "https://www.audible.com/pd/2001-A-Space-Odyssey-Audiobook/B0722XVYY2",
    }
    
    downloader = PlaywrightCoverDownloader()
    downloader.run(AUDIOBOOK_URLS)


if __name__ == "__main__":
    main()

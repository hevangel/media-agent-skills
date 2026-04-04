"""
Automated Audiobook Cover Downloader
Searches for and downloads missing audiobook covers, then embeds them.
"""

import json
import os
import re
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, quote_plus
import base64


# Try to import mutagen for embedding covers
try:
    from mutagen import File as MutagenFile
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.flac import FLAC, Picture
    from mutagen.oggvorbis import OggVorbis
    from mutagen.id3 import ID3, APIC
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not available. Install with: uv add mutagen")


@dataclass
class DownloadResult:
    author: str
    title: str
    path: str
    success: bool
    image_url: Optional[str] = None
    file_saved: bool = False
    embedded_count: int = 0
    error: Optional[str] = None


class AutomatedCoverDownloader:
    def __init__(self, scan_results_file: str = "audiobook_scan_results.json"):
        self.scan_results_file = scan_results_file
        self.results: List[DownloadResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def load_missing_covers(self) -> List[Dict]:
        """Load audiobooks missing covers."""
        with open(self.scan_results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get audiobooks without any cover (file or embedded)
        missing = [
            ab for ab in data['audiobooks']
            if not ab.get('has_cover', False) and not ab.get('has_embedded_cover', False)
        ]
        
        print(f"Loaded {len(missing)} audiobooks missing covers")
        return missing
    
    def search_for_cover_url(self, author: str, title: str) -> Optional[str]:
        """
        Search for cover image URL.
        This is a placeholder - you'll need to implement actual search logic.
        """
        # Clean up search terms
        author_clean = re.sub(r'[^\w\s]', '', author).strip()
        title_clean = re.sub(r'[^\w\s]', '', title).strip()
        
        # Build search query
        search_query = f'"{author_clean}" "{title_clean}" audiobook cover'
        
        print(f"  Search query: {search_query}")
        
        # Here you would implement actual web search
        # For now, return None - will be manually provided
        return None
    
    def extract_image_urls_from_audible(self, audible_url: str) -> Optional[str]:
        """Extract cover image URL from Audible page."""
        try:
            response = self.session.get(audible_url, timeout=15)
            response.raise_for_status()
            
            # Look for image URLs in the HTML
            content = response.text
            
            # Audible typically uses specific patterns for cover images
            # Look for high-res cover images
            patterns = [
                r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*bc-pub-block[^"]*"',
                r'<img[^>]*class="[^"]*bc-pub-block[^"]*"[^>]*src="([^"]*)"',
                r'"image":"([^"]*\.jpg)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Return the first match, preferring larger images
                    for match in matches:
                        if '500' in match or 'large' in match or '._SL' in match:
                            return match
                    return matches[0]
            
            return None
            
        except Exception as e:
            print(f"  Error extracting from Audible: {e}")
            return None
    
    def download_image(self, url: str, save_path: str) -> bool:
        """Download image from URL."""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # Verify it's an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type.lower():
                print(f"  ✗ Not an image: {content_type}")
                return False
            
            # Save the image
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024
            print(f"  ✓ Downloaded: {file_size:.1f} KB -> {save_path}")
            return True
            
        except Exception as e:
            print(f"  ✗ Download failed: {str(e)[:100]}")
            return False
    
    def embed_cover_in_file(self, audio_file_path: str, cover_image_path: str) -> bool:
        """Embed cover art into an audio file."""
        if not MUTAGEN_AVAILABLE:
            return False
        
        try:
            # Read cover image
            with open(cover_image_path, 'rb') as f:
                cover_data = f.read()
            
            audio = MutagenFile(audio_file_path)
            if audio is None:
                return False
            
            # Embed based on file type
            if isinstance(audio, MP4):
                audio.tags['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
                audio.save()
                return True
            
            elif isinstance(audio, MP3):
                if audio.tags is None:
                    audio.add_tags()
                
                audio.tags.delall('APIC')
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=cover_data
                ))
                audio.save()
                return True
            
            elif isinstance(audio, FLAC):
                audio.clear_pictures()
                picture = Picture()
                picture.data = cover_data
                picture.type = 3  # Front cover
                picture.mime = 'image/jpeg'
                audio.add_picture(picture)
                audio.save()
                return True
            
            elif isinstance(audio, OggVorbis):
                picture = Picture()
                picture.data = cover_data
                picture.type = 3
                picture.mime = 'image/jpeg'
                
                picture_data = base64.b64encode(picture.write()).decode('ascii')
                audio['metadata_block_picture'] = picture_data
                audio.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"    Error embedding: {str(e)[:80]}")
            return False
    
    def process_audiobook(self, audiobook: Dict, image_url: str) -> DownloadResult:
        """Process a single audiobook - download and embed cover."""
        author = audiobook['author']
        title = audiobook['title']
        path = audiobook['path']
        
        print(f"\n{'='*70}")
        print(f"Processing: {author} - {title}")
        print(f"{'='*70}")
        
        # Download cover to file
        cover_path = os.path.join(path, "cover.jpg")
        file_saved = self.download_image(image_url, cover_path)
        
        if not file_saved:
            return DownloadResult(
                author=author,
                title=title,
                path=path,
                success=False,
                image_url=image_url,
                error="Failed to download image"
            )
        
        # Embed cover in audio files
        embedded_count = 0
        if MUTAGEN_AVAILABLE:
            print(f"  Embedding cover in audio files...")
            audio_files = audiobook.get('audio_files', [])
            
            for i, audio_file in enumerate(audio_files[:5], 1):  # First 5 files only for efficiency
                audio_path = os.path.join(path, audio_file)
                if self.embed_cover_in_file(audio_path, cover_path):
                    embedded_count += 1
                    print(f"    ✓ Embedded in: {audio_file}")
                else:
                    print(f"    ✗ Failed: {audio_file}")
            
            if len(audio_files) > 5:
                print(f"    (Skipped {len(audio_files) - 5} remaining files)")
        else:
            print(f"  ⚠ Mutagen not available - skipping embedding")
        
        return DownloadResult(
            author=author,
            title=title,
            path=path,
            success=True,
            image_url=image_url,
            file_saved=file_saved,
            embedded_count=embedded_count
        )
    
    def save_results(self, filename: str = "cover_download_results.json"):
        """Save results to JSON."""
        data = {
            "total_processed": len(self.results),
            "successful": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "total_files_embedded": sum(r.embedded_count for r in self.results),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "results": [
                {
                    "author": r.author,
                    "title": r.title,
                    "path": r.path,
                    "success": r.success,
                    "image_url": r.image_url,
                    "file_saved": r.file_saved,
                    "embedded_count": r.embedded_count,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"Results saved to: {filename}")
        print(f"{'='*70}")
    
    def generate_report(self) -> str:
        """Generate summary report."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        total_embedded = sum(r.embedded_count for r in self.results)
        
        report = f"""
# Audiobook Cover Download Report

## Summary
- Total Processed: {total}
- Successfully Downloaded: {successful} ({successful/total*100:.1f}% if total else 0)
- Failed: {failed} ({failed/total*100:.1f}% if total else 0)
- Total Files with Embedded Covers: {total_embedded}

## Successful Downloads
"""
        
        for r in self.results:
            if r.success:
                report += f"\n✓ **{r.author}** - {r.title}\n"
                report += f"  - File saved: {r.file_saved}\n"
                report += f"  - Embedded in: {r.embedded_count} audio files\n"
                report += f"  - Path: `{r.path}`\n"
        
        if failed > 0:
            report += "\n## Failed Downloads\n"
            for r in self.results:
                if not r.success:
                    report += f"\n✗ **{r.author}** - {r.title}\n"
                    report += f"  - Error: {r.error}\n"
        
        return report


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║     AUTOMATED AUDIOBOOK COVER DOWNLOADER                           ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    if not MUTAGEN_AVAILABLE:
        print("⚠ WARNING: mutagen library not found!")
        print("  Install it with: uv add mutagen")
        print("  Covers will be saved as files but not embedded in audio files.\n")
    
    downloader = AutomatedCoverDownloader()
    missing = downloader.load_missing_covers()
    
    print(f"\nTotal audiobooks missing covers: {len(missing)}")
    print("\nThis tool will:")
    print("  1. Search for cover images online")
    print("  2. Download covers and save as cover.jpg")
    print("  3. Embed covers into audio files (if mutagen available)")
    print("\nReady to process!")


if __name__ == "__main__":
    main()

"""
Interactive Audiobook Cover Finder
Uses web search to find and download audiobook covers.
"""

import json
import os
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional
import re


class InteractiveCoverFinder:
    def __init__(self, scan_results_file: str = "audiobook_scan_results.json"):
        self.scan_results_file = scan_results_file
        self.missing_covers = []
        self.download_log = []
        
    def load_missing_covers(self) -> List[Dict]:
        """Load audiobooks missing covers."""
        with open(self.scan_results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.missing_covers = [ab for ab in data['audiobooks'] if not ab['has_cover']]
        return self.missing_covers
    
    def get_search_query(self, author: str, title: str) -> str:
        """Generate search query for cover image."""
        # Clean up special characters
        author_clean = re.sub(r'[^\w\s-]', '', author)
        title_clean = re.sub(r'[^\w\s-]', '', title)
        
        return f'"{author_clean}" "{title_clean}" audiobook cover art'
    
    def download_image(self, url: str, save_path: str) -> bool:
        """Download an image from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # Check if it's an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type.lower():
                print(f"  ✗ Not an image: {content_type}")
                return False
            
            # Save the image
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024  # Size in KB
            print(f"  ✓ Downloaded: {file_size:.1f} KB")
            return True
            
        except Exception as e:
            print(f"  ✗ Download failed: {str(e)[:100]}")
            return False
    
    def process_single_audiobook(self, audiobook: Dict, image_url: str) -> bool:
        """Download cover for a single audiobook."""
        path = audiobook['path']
        save_path = os.path.join(path, "cover.jpg")
        
        print(f"\nDownloading cover for: {audiobook['author']} - {audiobook['title']}")
        print(f"  URL: {image_url}")
        
        success = self.download_image(image_url, save_path)
        
        self.download_log.append({
            'author': audiobook['author'],
            'title': audiobook['title'],
            'path': path,
            'image_url': image_url,
            'success': success,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return success
    
    def show_missing_covers_summary(self):
        """Show summary of missing covers."""
        print(f"\n{'='*70}")
        print(f"AUDIOBOOKS MISSING COVERS: {len(self.missing_covers)}")
        print(f"{'='*70}\n")
        
        # Group by author
        by_author = {}
        for ab in self.missing_covers:
            author = ab['author']
            if author not in by_author:
                by_author[author] = []
            by_author[author].append(ab['title'])
        
        for i, (author, titles) in enumerate(sorted(by_author.items())[:20], 1):
            print(f"{i:2}. {author} ({len(titles)} book{'s' if len(titles) > 1 else ''})")
            for title in titles[:3]:
                print(f"    - {title}")
            if len(titles) > 3:
                print(f"    ... and {len(titles) - 3} more")
        
        if len(by_author) > 20:
            print(f"\n... and {len(by_author) - 20} more authors")
    
    def save_download_log(self, filename: str = "cover_download_log.json"):
        """Save download log to file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'total_attempts': len(self.download_log),
                'successful': sum(1 for log in self.download_log if log['success']),
                'failed': sum(1 for log in self.download_log if not log['success']),
                'downloads': self.download_log
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nDownload log saved to: {filename}")
    
    def interactive_mode(self):
        """Run in interactive mode for manual selection."""
        self.show_missing_covers_summary()
        
        print(f"\n{'='*70}")
        print("INTERACTIVE MODE")
        print("You can manually search for covers and provide image URLs")
        print(f"{'='*70}\n")
        
        print("Type 'list' to see the full list")
        print("Type 'search <number>' to get search query for an audiobook")
        print("Type 'download <number> <url>' to download a cover")
        print("Type 'quit' to exit")
        print()


def main():
    """Main entry point."""
    finder = InteractiveCoverFinder()
    finder.load_missing_covers()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║         AUDIOBOOK COVER FINDER & DOWNLOADER                   ║
╚═══════════════════════════════════════════════════════════════╝

This tool helps you find and download missing audiobook covers.

Next Steps:
1. Use web search to find cover images for audiobooks
2. Provide the image URL to download the cover
3. The cover will be saved as 'cover.jpg' in the audiobook directory

Total audiobooks missing covers: {len(finder.missing_covers)}
""")
    
    finder.show_missing_covers_summary()
    
    print(f"\n{'='*70}")
    print("To download a cover, you'll need to:")
    print("1. Search for the audiobook cover online (use DuckDuckGo)")
    print("2. Get the direct URL to the cover image")
    print("3. Use the downloader to save it")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

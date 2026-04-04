"""
Audiobook Cover Downloader
Downloads missing audiobook covers by searching the web.
"""

import json
import os
import re
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CoverDownloadResult:
    author: str
    title: str
    success: bool
    image_url: Optional[str] = None
    save_path: Optional[str] = None
    error: Optional[str] = None


class AudiobookCoverDownloader:
    def __init__(self, scan_results_file: str = "audiobook_scan_results.json"):
        self.scan_results_file = scan_results_file
        self.results: List[CoverDownloadResult] = []
        
    def load_missing_covers(self) -> List[Dict]:
        """Load the list of audiobooks missing covers."""
        with open(self.scan_results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        missing = [ab for ab in data['audiobooks'] if not ab['has_cover']]
        print(f"Loaded {len(missing)} audiobooks missing covers")
        return missing
    
    def search_audible_cover(self, author: str, title: str) -> Optional[str]:
        """
        Search for cover image URL on Audible.
        Returns the URL of the cover image if found.
        """
        try:
            # Clean up the search terms
            search_query = f"{author} {title} audible audiobook"
            
            # Use DuckDuckGo to search for Audible pages
            # This is a placeholder - actual implementation would use MCP DuckDuckGo
            print(f"Searching: {search_query}")
            
            # For now, return None - actual implementation would search and parse results
            return None
            
        except Exception as e:
            print(f"Error searching for {author} - {title}: {e}")
            return None
    
    def download_cover(self, url: str, save_dir: str, filename: str = "cover.jpg") -> bool:
        """Download cover image from URL."""
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Save the image
            save_path = os.path.join(save_dir, filename)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Downloaded: {save_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to download: {e}")
            return False
    
    def process_audiobook(self, audiobook: Dict, delay: float = 1.0) -> CoverDownloadResult:
        """Process a single audiobook - search and download cover."""
        author = audiobook['author']
        title = audiobook['title']
        path = audiobook['path']
        
        print(f"\nProcessing: {author} - {title}")
        
        # Search for cover URL
        image_url = self.search_audible_cover(author, title)
        
        if not image_url:
            return CoverDownloadResult(
                author=author,
                title=title,
                success=False,
                error="No cover image found"
            )
        
        # Download the cover
        success = self.download_cover(image_url, path)
        
        if success:
            save_path = os.path.join(path, "cover.jpg")
            result = CoverDownloadResult(
                author=author,
                title=title,
                success=True,
                image_url=image_url,
                save_path=save_path
            )
        else:
            result = CoverDownloadResult(
                author=author,
                title=title,
                success=False,
                image_url=image_url,
                error="Failed to download image"
            )
        
        # Be respectful - add delay between requests
        time.sleep(delay)
        
        return result
    
    def process_batch(self, limit: Optional[int] = None) -> List[CoverDownloadResult]:
        """Process a batch of audiobooks missing covers."""
        missing = self.load_missing_covers()
        
        if limit:
            missing = missing[:limit]
            print(f"Processing first {limit} audiobooks...")
        
        results = []
        for i, audiobook in enumerate(missing, 1):
            print(f"\n[{i}/{len(missing)}]", end=" ")
            result = self.process_audiobook(audiobook)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def save_results(self, filename: str = "cover_download_results.json"):
        """Save download results to a JSON file."""
        results_data = {
            "total_processed": len(self.results),
            "successful": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "results": [
                {
                    "author": r.author,
                    "title": r.title,
                    "success": r.success,
                    "image_url": r.image_url,
                    "save_path": r.save_path,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to {filename}")
        return results_data
    
    def generate_report(self) -> str:
        """Generate a summary report of the download process."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        
        report = f"""
# Cover Download Report

## Summary
- Total Processed: {total}
- Successfully Downloaded: {successful} ({successful/total*100:.1f}%)
- Failed: {failed} ({failed/total*100:.1f}%)

## Successful Downloads
"""
        
        for r in self.results:
            if r.success:
                report += f"\n- ✓ **{r.author}** - {r.title}\n  Saved to: `{r.save_path}`"
        
        report += "\n\n## Failed Downloads\n"
        
        for r in self.results:
            if not r.success:
                report += f"\n- ✗ **{r.author}** - {r.title}\n  Error: {r.error}"
        
        return report


def main():
    """Main entry point."""
    downloader = AudiobookCoverDownloader()
    
    # Process a small batch for testing (you can change the limit)
    print("Starting cover download process...")
    print("Note: This is a placeholder implementation.")
    print("Actual web searching will be implemented using DuckDuckGo MCP.")
    
    # Process first 5 audiobooks as a test
    downloader.process_batch(limit=5)
    
    # Save results
    downloader.save_results()
    
    # Generate report
    report = downloader.generate_report()
    
    with open("cover_download_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "="*60)
    print(report)
    print("="*60)


if __name__ == "__main__":
    main()

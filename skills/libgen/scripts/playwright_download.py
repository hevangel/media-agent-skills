"""
Download ebooks from Library Genesis using Playwright browser automation.

This script handles anti-bot measures by using a real browser to download files.
It's more reliable than direct HTTP requests for libgen downloads.

Falls back to direct HTTP download if Playwright fails (e.g. when GET opens mirrors page).

Usage:
    uv run playwright_download.py <md5_hash> --output "./downloads"
    uv run playwright_download.py <md5_hash> --output "./downloads" --headless

Prerequisites:
    uv pip install playwright
    playwright install chromium

Example:
    uv run playwright_download.py 0e5d19a33afebc900650bb582ad4df6a --output "./downloads"
"""
import argparse
import re
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def download_via_http(md5: str, output_dir: str, timeout: int = 120) -> str | None:
    """
    Try direct HTTP download from libgen mirrors.
    Fallback when Playwright fails (e.g. GET opens intermediate page).

    Fetches file.php page and extracts IPFS/Cloudflare direct links.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Step 1: Fetch file.php to get direct download links
    file_page_url = f"https://libgen.li/file.php?md5={md5}"
    try:
        print(f"  Fetching file info from libgen.li...")
        resp = requests.get(file_page_url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None

        html = resp.text
        # Extract direct download links: IPFS cloudflare, IPFS.io, or libgen mirror
        direct_link_patterns = [
            r'href="(https://cloudflare-ipfs\.com/ipfs/[^"]+)"',
            r'href="(https://gateway\.ipfs\.io/ipfs/[^"]+)"',
            r'href="(https://[^"]*libgen\.(?:li|pw)[^"]*/(?:main|get)\.php[^"]*)"',
            r'href="(https?://[^"]+\.epub)"',
        ]

        download_url = None
        for pattern in direct_link_patterns:
            match = re.search(pattern, html)
            if match:
                download_url = match.group(1).replace("&amp;", "&")
                break

        if not download_url:
            return None

        # Step 2: Download the file
        print(f"  Downloading from mirror...")
        file_resp = requests.get(download_url, headers=headers, allow_redirects=True, timeout=timeout)

        if file_resp.status_code != 200 or len(file_resp.content) < 1000:
            return None

        # Get filename from URL or use default
        fn_match = re.search(r'filename=([^&]+)', download_url)
        filename = fn_match.group(1).strip() if fn_match else f"{md5}.epub"
        filename = requests.utils.unquote(filename)

        save_path = output_path / filename
        save_path.write_bytes(file_resp.content)

        print(f"[OK] Downloaded: {save_path}")
        return str(save_path)

    except Exception as e:
        print(f"  HTTP download failed: {e}")
        return None


def download_from_libgen(
    md5: str,
    output_dir: str,
    headless: bool = False,
    timeout: int = 60000
) -> str | None:
    """
    Download a book from Library Genesis using Playwright.
    
    Args:
        md5: MD5 hash of the book to download
        output_dir: Directory to save the downloaded file
        headless: Run browser in headless mode (default: False for debugging)
        timeout: Download timeout in milliseconds (default: 60000)
        
    Returns:
        Path to the downloaded file, or None if download failed
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    url = f"https://libgen.li/ads.php?md5={md5}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # Wait for the page to load
            time.sleep(2)
            
            # Look for the GET button - it's typically at the top of the page
            # The button might have different selectors on different pages
            get_button_selectors = [
                'a:has-text("GET")',
                'a[href*="get.php"]',
                'input[value="GET"]',
                'button:has-text("GET")',
                '.record_get a',
                'h2 a:has-text("GET")',
            ]
            
            download = None
            
            for selector in get_button_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        print(f"Found download button with selector: {selector}")
                        
                        # Start waiting for download before clicking
                        with page.expect_download(timeout=timeout) as download_info:
                            element.click()
                        
                        download = download_info.value
                        break
                except Exception:
                    continue
            
            if download:
                # Save the download to the output directory
                suggested_filename = download.suggested_filename
                save_path = output_path / suggested_filename
                download.save_as(str(save_path))
                
                print(f"[OK] Downloaded: {save_path}")
                print(f"  Size: {save_path.stat().st_size / 1024 / 1024:.2f} MB")
                return str(save_path)
            else:
                print("[X] Playwright could not capture download, trying HTTP fallback...")
                
        except PlaywrightTimeoutError as e:
            print(f"[X] Timeout error: {e}")
            print("  Trying HTTP fallback...")
        except Exception as e:
            print(f"[X] Playwright error: {e}")
            print("  Trying HTTP fallback...")
        finally:
            browser.close()

    # Fallback to direct HTTP download
    return download_via_http(md5, output_dir, timeout=timeout // 1000)


def download_from_annas_archive(
    md5: str,
    output_dir: str,
    headless: bool = False,
    timeout: int = 60000
) -> str | None:
    """
    Download a book from Anna's Archive as a fallback.
    
    Note: Anna's Archive uses DDOS-GUARD which may require manual CAPTCHA solving.
    
    Args:
        md5: MD5 hash of the book to download
        output_dir: Directory to save the downloaded file
        headless: Run browser in headless mode
        timeout: Download timeout in milliseconds
        
    Returns:
        Path to the downloaded file, or None if download failed
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    url = f"https://annas-archive.org/md5/{md5}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # Wait for possible CAPTCHA
            time.sleep(3)
            
            # Look for libgen.li link on the page
            libgen_link = page.locator('a[href*="libgen.li"]').first
            
            if libgen_link.is_visible(timeout=5000):
                print("Found libgen.li link, clicking...")
                libgen_link.click()
                page.wait_for_load_state("networkidle")
                
                # Now we should be on libgen.li, look for GET button
                with page.expect_download(timeout=timeout) as download_info:
                    page.locator('a:has-text("GET")').first.click()
                
                download = download_info.value
                suggested_filename = download.suggested_filename
                save_path = output_path / suggested_filename
                download.save_as(str(save_path))
                
                print(f"[OK] Downloaded: {save_path}")
                return str(save_path)
            else:
                print("[X] Could not find libgen.li link")
                print("  You may need to solve a CAPTCHA manually")
                return None
                
        except Exception as e:
            print(f"[X] Error: {e}")
            return None
        finally:
            browser.close()


def search_and_download(
    title: str,
    output_dir: str,
    author: str | None = None,
    format: str = "epub",
    headless: bool = False
) -> str | None:
    """
    Search for a book and download it in one step.
    
    Args:
        title: Book title to search for
        output_dir: Directory to save the downloaded file
        author: Author name filter (optional)
        format: Preferred format (default: epub)
        headless: Run browser in headless mode
        
    Returns:
        Path to the downloaded file, or None if not found/failed
    """
    from search_books import search_books
    
    print(f"Searching for: {title}" + (f" by {author}" if author else ""))
    
    results = search_books(title, author, format, limit=5)
    
    if not results:
        # Try without format filter
        results = search_books(title, author, limit=5)
    
    if not results:
        print("[X] Book not found in Library Genesis")
        return None
    
    book = results[0]
    print(f"Found: {book.title} by {book.author}")
    print(f"Format: {book.extension}, Size: {book.size}")
    print(f"MD5: {book.md5}")
    
    return download_from_libgen(book.md5, output_dir, headless=headless)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a book from Library Genesis using Playwright",
        epilog="Requires: uv pip install playwright && playwright install chromium"
    )
    parser.add_argument("md5", help="MD5 hash of the book to download")
    parser.add_argument("--output", "-o", default=".", help="Output directory (default: current)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--timeout", type=int, default=60000, help="Timeout in ms (default: 60000)")
    
    args = parser.parse_args()
    
    result = download_from_libgen(
        args.md5,
        args.output,
        headless=args.headless,
        timeout=args.timeout
    )
    
    if result:
        print(f"\nSuccess! File saved to: {result}")
    else:
        print("\nDownload failed. Try:")
        print("  1. Disable headless mode to debug")
        print("  2. Use a VPN if your ISP blocks libgen")
        print(f"  3. Download manually: https://libgen.li/ads.php?md5={args.md5}")

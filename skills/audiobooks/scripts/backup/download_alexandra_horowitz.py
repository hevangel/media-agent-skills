"""
Download cover for Alexandra Horowitz - Inside of a Dog using Playwright
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

# Book details
author = "Alexandra Horowitz"
title = "Inside of a Dog"
audiobook_path = Path(r"E:\audiobooks\Alexandra Horowitz\Inside of a Dog - What Dogs See, Smell, and Know")

print(f"Downloading cover for: {title} by {author}")
print(f"Audiobook path: {audiobook_path}")

# Create covers directory
covers_dir = Path(r"c:\Users\hevan\work\ai_agents\.playwright-covers")
covers_dir.mkdir(exist_ok=True)

# Launch browser
with sync_playwright() as p:
    print("\n→ Launching browser...")
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Navigate to Audible search
    search_query = f"{author} {title}"
    print(f"→ Searching Audible: {search_query}")
    page.goto(f"https://www.audible.com/search?keywords={search_query}")
    time.sleep(2)
    
    # Click first result
    print("→ Clicking first search result...")
    first_result = page.locator(".productListItem").first
    first_result.click()
    time.sleep(2)
    
    print("→ Opened product page")
    
    # Screenshot the cover image
    cover_element = page.locator("img.bc-image-inset-border").first
    cover_path = covers_dir / "alexandra_horowitz_inside_of_a_dog_cover.png"
    
    print(f"→ Saving cover to: {cover_path}")
    cover_element.screenshot(path=str(cover_path))
    
    print("✓ Cover downloaded successfully!")
    print(f"\nCover saved to: {cover_path}")
    
    browser.close()

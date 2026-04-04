import asyncio
import json
import aiohttp
from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token

async def update_author_photos():
    server_url = "http://localhost/audiobookshelf"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlJZCI6IjRlN2YyMjcxLTBmZDktNDQ5Mi1iYTkxLTYyMzU3NzdhZjFmMyIsIm5hbWUiOiJob3JhY2UiLCJ0eXBlIjoiYXBpIiwiaWF0IjoxNzY3MDUwMTUwfQ.aIAXERadYXh10dJ7eXjoIvC8P4PWjOGGc4RNTZV8Cqk"
    audiobooks_library_id = "d852a24d-c105-4b71-a0ab-5bc5070e49d5"
    
    # Load authors from JSON
    with open('authors.json', 'r') as f:
        authors_data = json.load(f)
    
    print("=" * 80)
    print("UPDATING AUTHOR PHOTOS IN AUDIOBOOKSHELF")
    print("=" * 80)
    print(f"\nLoaded {len(authors_data)} authors from authors.json\n")
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=server_url,
            token=api_key
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        
        # Get all authors in the library
        library_authors = await abs_client.get_library_authors(library_id=audiobooks_library_id)
        
        print(f"Found {len(library_authors)} authors in Audiobookshelf library\n")
        
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        
        for author_info in authors_data:
            author_name = author_info.get('name')
            image_url = author_info.get('image_url')
            author_id = author_info.get('id')
            
            if not image_url:
                print(f"[SKIP] {author_name}: No image URL in JSON")
                skipped_count += 1
                continue
            
            # Find matching author in library
            matching_author = None
            for lib_author in library_authors:
                if lib_author.name.lower() == author_name.lower():
                    matching_author = lib_author
                    break
            
            if not matching_author:
                print(f"[SKIP] {author_name}: Not found in library")
                skipped_count += 1
                continue
            
            # Update author photo via PATCH endpoint
            url = f"{server_url}/api/authors/{matching_author.id_}"
            
            payload = {
                'name': author_name,
                'image': image_url
            }
            
            print(f"Updating: {author_name}")
            print(f"  Author ID: {matching_author.id_}")
            print(f"  Image URL: {image_url}")
            
            try:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
                async with session.patch(url, headers=headers, json=payload) as response:
                    if response.status in [200, 204]:
                        print(f"  [OK] Successfully updated!")
                        updated_count += 1
                    else:
                        error_text = await response.text()
                        print(f"  [FAIL] Failed with status {response.status}")
                        if error_text:
                            print(f"         Error: {error_text[:100]}")
                        failed_count += 1
            except Exception as e:
                print(f"  [FAIL] Exception: {str(e)[:100]}")
                failed_count += 1
            
            print()
        
        print("=" * 80)
        print("UPDATE SUMMARY")
        print("=" * 80)
        print(f"[OK] Successfully updated: {updated_count}")
        print(f"[SKIP] Skipped: {skipped_count}")
        print(f"[FAIL] Failed: {failed_count}")
        print(f"Total processed: {updated_count + skipped_count + failed_count}")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(update_author_photos())

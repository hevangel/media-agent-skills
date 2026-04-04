import asyncio
import aiohttp
import json

async def update_asimov_series():
    server_url = "http://localhost/audiobookshelf"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlJZCI6IjRlN2YyMjcxLTBmZDktNDQ5Mi1iYTkxLTYyMzU3NzdhZjFmMyIsIm5hbWUiOiJob3JhY2UiLCJ0eXBlIjoiYXBpIiwiaWF0IjoxNzY3MDUwMTUwfQ.aIAXERadYXh10dJ7eXjoIvC8P4PWjOGGc4RNTZV8Cqk"
    audiobooks_library_id = "d852a24d-c105-4b71-a0ab-5bc5070e49d5"
    
    # Book mapping with correct order
    books = [
        {
            'id': 'adec6290-68f9-4b49-9043-530e7271d6a0',
            'title': 'Foundation',
            'sequence': '1'
        },
        {
            'id': 'd4bc97f4-1c62-4175-8d15-8a99b713d13e',
            'title': 'Second Foundation',
            'sequence': '3'
        },
        {
            'id': '08b2eceb-77bc-484f-a849-234466425c04',
            'title': "Foundation's Edge",
            'sequence': '4'
        },
        {
            'id': '937ddfd2-0cbe-425b-b80a-d14f79c8b6b9',
            'title': 'Foundation and Earth',
            'sequence': '5'
        },
        {
            'id': '98f85046-d633-48a5-8668-b259546d9aef',
            'title': 'Prelude to Foundation',
            'sequence': '6'
        },
        {
            'id': 'c99863a1-4178-4483-87b4-f30feeac97b5',
            'title': 'Forward the Foundation',
            'sequence': '7'
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        print("Updating series metadata for all Asimov Foundation books...")
        print("=" * 80)
        
        for book in books:
            # Update metadata via PATCH endpoint
            url = f"{server_url}/api/items/{book['id']}/media"
            
            payload = {
                'metadata': {
                    'series': [
                        {
                            'name': 'Foundation',
                            'sequence': book['sequence']
                        }
                    ]
                }
            }
            
            print(f"\nUpdating: {book['title']}")
            print(f"  Item ID: {book['id']}")
            print(f"  Series: Foundation (Book {book['sequence']})")
            
            async with session.patch(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✓ Successfully updated!")
                else:
                    error_text = await response.text()
                    print(f"  ✗ Failed with status {response.status}: {error_text}")
        
        print("\n" + "=" * 80)
        print("Update complete!")

if __name__ == "__main__":
    asyncio.run(update_asimov_series())

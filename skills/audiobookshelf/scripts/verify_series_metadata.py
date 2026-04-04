import asyncio
import aiohttp
from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token

async def verify_asimov_series():
    server_url = "http://localhost/audiobookshelf"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlJZCI6IjRlN2YyMjcxLTBmZDktNDQ5Mi1iYTkxLTYyMzU3NzdhZjFmMyIsIm5hbWUiOiJob3JhY2UiLCJ0eXBlIjoiYXBpIiwiaWF0IjoxNzY3MDUwMTUwfQ.aIAXERadYXh10dJ7eXjoIvC8P4PWjOGGc4RNTZV8Cqk"
    
    book_ids = [
        'adec6290-68f9-4b49-9043-530e7271d6a0',  # Book 1
        'd4bc97f4-1c62-4175-8d15-8a99b713d13e',  # Book 3
        '08b2eceb-77bc-484f-a849-234466425c04',  # Book 4
        '937ddfd2-0cbe-425b-b80a-d14f79c8b6b9',  # Book 5
        '98f85046-d633-48a5-8668-b259546d9aef',  # Book 6
        'c99863a1-4178-4483-87b4-f30feeac97b5',  # Book 7
    ]
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=server_url,
            token=api_key
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        
        print("Verifying series metadata for Asimov Foundation books...")
        print("=" * 80)
        
        series_names = set()
        
        for book_id in book_ids:
            item = await abs_client.get_library_item_book(book_id=book_id, expanded=True)
            
            print(f"\nTitle: {item.media.metadata.title}")
            print(f"Item ID: {item.id_}")
            
            if hasattr(item.media.metadata, 'series') and item.media.metadata.series:
                for series in item.media.metadata.series:
                    print(f"Series: {series.name} (Book {series.sequence})")
                    print(f"Series ID: {series.id_}")
                    series_names.add(series.name)
            else:
                print("Series: None")
            print("-" * 80)
        
        print(f"\n{'=' * 80}")
        print(f"\nSummary:")
        print(f"Total books checked: {len(book_ids)}")
        print(f"\nUnique series names found:")
        for series_name in sorted(series_names):
            print(f"  - {series_name}")

if __name__ == "__main__":
    asyncio.run(verify_asimov_series())

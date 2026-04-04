import asyncio
import aiohttp
from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token

async def get_asimov_metadata():
    server_url = "http://localhost/audiobookshelf"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlJZCI6IjRlN2YyMjcxLTBmZDktNDQ5Mi1iYTkxLTYyMzU3NzdhZjFmMyIsIm5hbWUiOiJob3JhY2UiLCJ0eXBlIjoiYXBpIiwiaWF0IjoxNzY3MDUwMTUwfQ.aIAXERadYXh10dJ7eXjoIvC8P4PWjOGGc4RNTZV8Cqk"
    audiobooks_library_id = "d852a24d-c105-4b71-a0ab-5bc5070e49d5"
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=server_url,
            token=api_key
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        
        library_authors = await abs_client.get_library_authors(library_id=audiobooks_library_id)
        
        asimov_author = None
        for author in library_authors:
            if "asimov" in author.name.lower():
                asimov_author = author
                print(f"Found author: {author.name}")
                print(f"Author ID: {author.id_}")
                print("\n" + "=" * 80 + "\n")
                break
        
        if not asimov_author:
            print("Author 'Isaac Asimov' not found in the Audiobooks library")
            return
        
        author_details = await abs_client.get_author(
            author_id=asimov_author.id_,
            include_items=True
        )
        
        print(f"Books by {asimov_author.name} - Full Metadata:\n")
        print("=" * 80)
        
        series_names = set()
        books_metadata = []
        
        for item in author_details.library_items:
            media = item.media
            metadata = media.metadata
            
            book_info = {
                'item_id': item.id_,
                'title': metadata.title,
                'subtitle': getattr(metadata, 'subtitle', None),
                'series': [],
                'published_year': getattr(metadata, 'published_year', None),
                'duration': media.duration if hasattr(media, 'duration') else None
            }
            
            if hasattr(metadata, 'series') and metadata.series:
                for series in metadata.series:
                    series_info = {
                        'id': series.id_,
                        'name': series.name,
                        'sequence': series.sequence
                    }
                    book_info['series'].append(series_info)
                    series_names.add(series.name)
            
            books_metadata.append(book_info)
            
            print(f"\nItem ID: {item.id_}")
            print(f"Title: {metadata.title}")
            if book_info['subtitle']:
                print(f"Subtitle: {book_info['subtitle']}")
            if book_info['series']:
                for series in book_info['series']:
                    print(f"Series: {series['name']} (Book {series['sequence']})")
                    print(f"Series ID: {series['id']}")
            if book_info['published_year']:
                print(f"Published: {book_info['published_year']}")
            if book_info['duration']:
                hours = book_info['duration'] / 3600
                print(f"Duration: {hours:.2f} hours")
            print("-" * 80)
        
        print(f"\n{'=' * 80}")
        print(f"\nSummary:")
        print(f"Total books: {len(books_metadata)}")
        print(f"\nUnique series names found:")
        for series_name in sorted(series_names):
            print(f"  - {series_name}")
        
        return books_metadata, series_names

if __name__ == "__main__":
    asyncio.run(get_asimov_metadata())

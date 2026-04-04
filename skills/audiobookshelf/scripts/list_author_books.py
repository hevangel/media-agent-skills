import asyncio
import aiohttp
from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token

async def list_asimov_books():
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
                print(f"Total books: {author.num_books if hasattr(author, 'num_books') else 'N/A'}")
                print("\n" + "=" * 80 + "\n")
                break
        
        if not asimov_author:
            print("Author 'Isaac Asimov' not found in the Audiobooks library")
            return
        
        author_details = await abs_client.get_author(
            author_id=asimov_author.id_,
            include_items=True
        )
        
        print(f"Books by {asimov_author.name}:\n")
        print("-" * 80)
        
        if hasattr(author_details, 'library_items') and author_details.library_items:
            for item in author_details.library_items:
                media = item.media
                print(f"Title: {media.metadata.title}")
                if hasattr(media.metadata, 'subtitle') and media.metadata.subtitle:
                    print(f"Subtitle: {media.metadata.subtitle}")
                if hasattr(media.metadata, 'series') and media.metadata.series:
                    for series in media.metadata.series:
                        print(f"Series: {series.name} (Book {series.sequence})")
                if hasattr(media.metadata, 'published_year') and media.metadata.published_year:
                    print(f"Published: {media.metadata.published_year}")
                if hasattr(media, 'duration') and media.duration:
                    hours = media.duration / 3600
                    print(f"Duration: {hours:.2f} hours")
                print("-" * 80)
            
            print(f"\nTotal: {len(author_details.library_items)} books")
        else:
            print("No books found for this author")

if __name__ == "__main__":
    asyncio.run(list_asimov_books())

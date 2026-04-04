import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token

load_dotenv()

async def list_libraries():
    server_url = os.getenv("AUDIOBOOKSHELF_HOST", "http://localhost/audiobookshelf")
    api_key = os.getenv("AUDIOBOOKSHELF_API_KEY")
    
    async with aiohttp.ClientSession() as session:
        session_config = SessionConfiguration(
            session=session,
            url=server_url,
            token=api_key
        )
        
        abs_client = await get_admin_client_by_token(session_config=session_config)
        
        libraries = await abs_client.get_all_libraries()
        
        print(f"\nFound {len(libraries)} libraries:\n")
        print("-" * 80)
        
        for library in libraries:
            print(f"Library ID: {library.id_}")
            print(f"Name: {library.name}")
            print(f"Type: {library.media_type}")
            if hasattr(library, 'stats') and library.stats:
                print(f"Total Items: {library.stats.total_items}")
                if hasattr(library.stats, 'total_size'):
                    size_gb = library.stats.total_size / (1024**3)
                    print(f"Total Size: {size_gb:.2f} GB")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(list_libraries())

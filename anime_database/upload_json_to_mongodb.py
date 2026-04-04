#!/usr/bin/env python3
"""
Script to upload anime-offline-database.json to MongoDB localhost server.
Creates a new collection named 'anime' and uploads all anime data.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, BulkWriteError
except ImportError:
    print("Error: pymongo is required. Install it with: uv add pymongo")
    exit(1)


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mongodb_upload.log'),
            logging.StreamHandler()
        ]
    )


def connect_to_mongodb(host: str = 'localhost', port: int = 27017, db_name: str = 'info') -> tuple:
    """
    Connect to MongoDB server and return client and database objects.
    
    Args:
        host: MongoDB host address
        port: MongoDB port number
        db_name: Database name to use
        
    Returns:
        Tuple of (client, database) objects
        
    Raises:
        ConnectionFailure: If unable to connect to MongoDB
    """
    try:
        client = MongoClient(host, port, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        database = client[db_name]
        logging.info(f"Successfully connected to MongoDB at {host}:{port}")
        return client, database
    except ConnectionFailure as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise


def load_anime_data(file_path: Path) -> Dict[str, Any]:
    """
    Load anime data from JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the loaded JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        logging.info(f"Loading anime data from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logging.info(f"Successfully loaded {len(data.get('data', []))} anime entries")
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format: {e}")
        raise


def prepare_anime_documents(anime_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare anime documents for MongoDB insertion.
    
    Args:
        anime_data: Raw anime data from JSON
        
    Returns:
        List of processed anime documents
    """
    documents = []
    
    # The anime-offline-database typically has a 'data' key containing the anime list
    anime_list = anime_data.get('data', [])
    
    for anime in anime_list:
        # Add any additional processing here if needed
        # For example, adding timestamps, normalizing data, etc.
        if isinstance(anime, dict):
            # Add upload timestamp
            anime['uploaded_at'] = None  # Will be set by MongoDB
            documents.append(anime)
    
    logging.info(f"Prepared {len(documents)} documents for insertion")
    return documents


def upload_to_mongodb(database, collection_name: str, documents: List[Dict[str, Any]], batch_size: int = 1000) -> None:
    """
    Upload documents to MongoDB collection in batches.
    
    Args:
        database: MongoDB database object
        collection_name: Name of the collection to create/use
        documents: List of documents to insert
        batch_size: Number of documents to insert per batch
    """
    collection = database[collection_name]
    
    # Drop existing collection if it exists (optional - remove if you want to append)
    if collection_name in database.list_collection_names():
        logging.info(f"Collection '{collection_name}' already exists. Dropping it...")
        collection.drop()
    
    logging.info(f"Creating collection '{collection_name}' and uploading {len(documents)} documents")
    
    # Insert documents in batches
    total_inserted = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            result = collection.insert_many(batch, ordered=False)
            total_inserted += len(result.inserted_ids)
            logging.info(f"Inserted batch {i//batch_size + 1}: {len(result.inserted_ids)} documents")
        except BulkWriteError as e:
            logging.error(f"Bulk write error in batch {i//batch_size + 1}: {e}")
            # Continue with next batch even if this one fails
            continue
    
    logging.info(f"Successfully inserted {total_inserted} documents into '{collection_name}' collection")
    
    # Create some useful indexes
    try:
        # Index on title for faster searches
        collection.create_index("title")
        logging.info("Created index on 'title' field")
        
        # Index on sources.mal_id if it exists (MyAnimeList ID)
        if any("sources" in doc for doc in documents[:10]):  # Check first few docs
            collection.create_index("sources.mal_id")
            logging.info("Created index on 'sources.mal_id' field")
            
        # Index on type if it exists
        if any("type" in doc for doc in documents[:10]):
            collection.create_index("type")
            logging.info("Created index on 'type' field")
            
    except Exception as e:
        logging.warning(f"Failed to create indexes: {e}")


def main():
    """Main function to orchestrate the upload process."""
    setup_logging()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Upload anime-offline-database JSON to MongoDB'
    )
    parser.add_argument(
        'json_file',
        nargs='?',
        default='anime-offline-database-minified.json',
        help='Path to the anime database JSON file (default: anime-offline-database-minified.json)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='MongoDB host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=27017,
        help='MongoDB port (default: 27017)'
    )
    parser.add_argument(
        '--database',
        default='info',
        help='Database name (default: info)'
    )
    parser.add_argument(
        '--collection',
        default='anime',
        help='Collection name (default: anime)'
    )
    
    args = parser.parse_args()
    
    # Configuration
    json_file_path = Path(args.json_file)
    if not json_file_path.is_absolute():
        json_file_path = Path(__file__).parent / json_file_path
    
    mongodb_host = args.host
    mongodb_port = args.port
    database_name = args.database
    collection_name = args.collection
    
    try:
        # Connect to MongoDB
        client, database = connect_to_mongodb(mongodb_host, mongodb_port, database_name)
        
        # Load anime data
        anime_data = load_anime_data(json_file_path)
        
        # Prepare documents
        documents = prepare_anime_documents(anime_data)
        
        if not documents:
            logging.warning("No documents to upload")
            return
        
        # Upload to MongoDB
        upload_to_mongodb(database, collection_name, documents)
        
        # Display collection info
        collection = database[collection_name]
        total_count = collection.count_documents({})
        logging.info(f"Upload completed! Collection '{collection_name}' now contains {total_count} documents")
        
        # Display some sample documents
        logging.info("Sample documents:")
        for i, doc in enumerate(collection.find().limit(3)):
            # Remove _id for cleaner display
            doc.pop('_id', None)
            logging.info(f"Sample {i+1}: {json.dumps(doc, indent=2, ensure_ascii=False)[:200]}...")
        
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        return 1
    
    finally:
        if 'client' in locals():
            client.close()
            logging.info("MongoDB connection closed")
    
    return 0


if __name__ == "__main__":
    exit(main())

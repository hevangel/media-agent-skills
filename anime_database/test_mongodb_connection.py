#!/usr/bin/env python3
"""
Simple script to test MongoDB connection before running the main upload.
"""

def test_mongodb_connection():
    """Test if MongoDB is running and accessible."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        
        print("Testing MongoDB connection...")
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # Get server info
        server_info = client.server_info()
        print(f"MongoDB version: {server_info['version']}")
        
        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")
        
        client.close()
        return True
        
    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\nMake sure MongoDB is running on localhost:27017")
        print("You can start MongoDB with:")
        print("  - Windows: net start MongoDB")
        print("  - Manual: mongod")
        return False
    except ImportError:
        print("❌ pymongo is not installed. Run: uv sync")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    test_mongodb_connection()

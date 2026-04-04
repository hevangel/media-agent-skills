# MongoDB Upload Script

This script uploads the `anime-offline-database.json` file to a MongoDB server running on localhost.

## Prerequisites

1. **MongoDB Server**: Make sure you have MongoDB running on localhost:27017
   - Install MongoDB Community Edition from: https://www.mongodb.com/try/download/community
   - Start the MongoDB service

2. **Python Dependencies**: The required dependencies are already included in the project:
   - `pymongo>=4.6.0` - MongoDB driver for Python
   - `dnspython` - DNS toolkit (automatically installed with pymongo)

## Usage

1. Make sure your MongoDB server is running:
   ```bash
   # On Windows (if MongoDB is installed as a service)
   net start MongoDB
   
   # Or run manually
   mongod
   ```

2. Download the anime database file using GitHub CLI:
   ```bash
   # Download the minified anime database from the latest release
   gh release download --repo manami-project/anime-offline-database --pattern "anime-offline-database-minified.json"
   ```
   
   Note: Make sure you have GitHub CLI installed. You can install it from: https://cli.github.com/

3. Run the upload script:
   ```bash
   # From the anime_database directory
   uv run python upload_json_to_mongodb.py
   
   # Or from the project root
   uv run python anime_database/upload_json_to_mongodb.py
   ```

## What the script does

1. **Connects** to MongoDB server at `localhost:27017`
2. **Creates** a database named `info`
3. **Creates** a collection named `anime`
4. **Loads** the `anime-offline-database.json` file
5. **Uploads** all anime data to the MongoDB collection in batches
6. **Creates indexes** on commonly searched fields:
   - `title` - for searching by anime title
   - `sources.mal_id` - for MyAnimeList ID lookups
   - `type` - for filtering by anime type (TV, Movie, etc.)

## Configuration

You can modify these settings in the `main()` function:

- `mongodb_host`: MongoDB server address (default: "localhost")
- `mongodb_port`: MongoDB server port (default: 27017)
- `database_name`: Database name to create (default: "anime_database")
- `collection_name`: Collection name to create (default: "anime")

## Logging

The script creates a log file `mongodb_upload.log` with detailed information about the upload process.

## Verification

After running the script, you can verify the upload using MongoDB Compass or the MongoDB shell:

```javascript
// Connect to the database
use anime_database

// Check collection size
db.anime.countDocuments()

// View sample documents
db.anime.find().limit(3).pretty()

// Search for specific anime
db.anime.find({"title": "Naruto"})
```

## Error Handling

The script includes comprehensive error handling for:
- MongoDB connection failures
- File not found errors
- JSON parsing errors
- Bulk write failures during upload

Check the log file for detailed error information if the upload fails.

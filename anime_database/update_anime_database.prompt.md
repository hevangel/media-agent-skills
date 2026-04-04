---
mode: 'agent'
tools: ['vscode', 'execute', 'read', 'edit', 'search', 'web', 'duckduckgo/*', 'filesystem/*', 'agent', 'todo']
description: 'organize anime files'
---

# Updating the Anime Database in MongoDB
1. Use the Github CLI to manami-project/anime-offline-database download the anime-offline-database-minified.json file from the releases page.
2. Use the upload_json_to_mongodb.py script in the anime_database directory to upload the downloaded JSON file to your local MongoDB server. 
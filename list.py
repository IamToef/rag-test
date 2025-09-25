import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load variables from .env file
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("Missing QDRANT_URL or QDRANT_API_KEY in .env file")

# Connect to Qdrant
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# List collections
collections = client.get_collections()

print("📂 Existing collections in Qdrant:")
for c in collections.collections:
    print("-", c.name)

collection_name = input("Input a collection: ")  # 👈 change this
if collection_name==None or collection_name.strip()=="":
    print("No collection name provided, exiting.")
    exit(0)
elif collection_name == "all":
    for c in collections.collections:
        client.delete_collection(collection_name=c.name)
        print(f"🗑️ Deleted collection: {c.name}")
else:
    client.delete_collection(collection_name=collection_name)

print(f"🗑️ Deleted collection: {collection_name}")

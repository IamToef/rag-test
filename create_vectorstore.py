from utils.ingest import build_vectorstore
from qdrant_client import QdrantClient

folder_path = "data"
collection_name = "docs"

client = QdrantClient(host="localhost", port=6333)

# Build vectorstore
vectorstore = build_vectorstore(folder_path, collection_name=collection_name)
print(f"Vectorstore '{collection_name}' đã được tạo thành công!")

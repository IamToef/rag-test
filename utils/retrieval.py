import os
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from .embedder import get_embedder

# Load biến môi trường từ file .env
load_dotenv()

def get_vectorstore(collection_name: str = "docs", use_cloud: bool = False) -> QdrantVectorStore:
    """
    Load lại vectorstore từ Qdrant (chỉ đọc, không build lại).
    Có thể chạy với Qdrant local hoặc Qdrant Cloud.
    """
    embeddings = get_embedder()

    if use_cloud:
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        if not url or not api_key:
            raise ValueError("Thiếu QDRANT_URL hoặc QDRANT_API_KEY trong .env")
        client = QdrantClient(url=url, api_key=api_key)
    else:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", 6333))
        client = QdrantClient(host=host, port=port)

    # Check collection tồn tại
    collections = client.get_collections().collections
    if not any(c.name == collection_name for c in collections):
        raise ValueError(
            f"Collection '{collection_name}' chưa tồn tại. Hãy chạy ingest.py trước."
        )

    print(f"Loading vectorstore từ collection '{collection_name}'")
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )

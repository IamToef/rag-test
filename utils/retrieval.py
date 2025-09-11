from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from .embedder import get_embedder

def get_vectorstore(collection_name: str = "docs") -> QdrantVectorStore:
    """
    Load lại vectorstore từ Qdrant (chỉ đọc, không build lại)
    """
    embeddings = get_embedder()
    client = QdrantClient(host="localhost", port=6333)

    # Check collection tồn tại
    collections = client.get_collections().collections
    if not any(c.name == collection_name for c in collections):
        raise ValueError(
            f"Collection '{collection_name}' chưa tồn tại. Hãy chạy build_vectorstore trước."
        )

    print(f"Loading vectorstore từ collection '{collection_name}'")
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )

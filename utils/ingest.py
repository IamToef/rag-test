from typing import Optional
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from .embedder import get_embedder
from .chunker import chunk_documents
from .loader import load_documents_from_folder


def ensure_collection_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
) -> None:
    """
    Đảm bảo collection tồn tại trong Qdrant, nếu chưa có thì tạo mới.
    """
    collections = client.get_collections().collections
    if not any(c.name == collection_name for c in collections):
        print(f"Tạo collection mới: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )
    else:
        print(f"Collection '{collection_name}' đã tồn tại")

def build_vectorstore(
    folder_path: str = "data",
    collection_name: str = "docs",
    host: str = "localhost",
    port: int = 6333,
) -> QdrantVectorStore:
    """
    Build hoặc thêm tài liệu mới vào vectorstore trong Qdrant.
    """
    # Khởi tạo embedder và Qdrant client
    embeddings = get_embedder()
    client = QdrantClient(host=host, port=port)

    # Lấy dimension từ 1 embedding mẫu
    test_vector = embeddings.embed_query("dimension check")
    vector_size = len(test_vector)

    # Đảm bảo collection đã tồn tại
    ensure_collection_exists(
        client=client,
        collection_name=collection_name,
        vector_size=vector_size,
    )

    # Load tài liệu
    print(f"Đang load tài liệu từ: {folder_path}")
    docs = load_documents_from_folder(folder_path)
    if not docs:
        raise ValueError(f"Không tìm thấy tài liệu trong {folder_path}")

    # Chunk tài liệu
    chunks = chunk_documents(docs)
    if not chunks:
        raise ValueError("Chunking thất bại - không có chunk nào")
    print(f"Đã split thành {len(chunks)} chunks")

    # Thêm vào vectorstore (dùng host/port thay vì client)
    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        host=host,
        port=port,
        collection_name=collection_name,
    )
    print(f"Vectorstore đã được cập nhật trong collection '{collection_name}'")

    return vectorstore

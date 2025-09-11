import hashlib
import logging
from typing import List, Set

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from .embedder import get_embedder
from .chunker import chunk_documents
from .loader import load_documents_from_folder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def ensure_collection_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
) -> None:
    """Đảm bảo collection tồn tại trong Qdrant, nếu chưa có thì tạo mới."""
    collections = client.get_collections().collections
    if not any(c.name == collection_name for c in collections):
        logger.info(f"Tạo collection mới: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )
    else:
        logger.info(f"Collection '{collection_name}' đã tồn tại")


def get_chunk_id(text: str) -> str:
    """Tạo ID duy nhất cho mỗi chunk dựa trên nội dung"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_existing_chunk_ids(client: QdrantClient, collection_name: str) -> Set[str]:
    """Lấy set ID của các chunk đã có trong collection"""
    existing_ids: Set[str] = set()
    try:
        scroll = client.scroll(collection_name=collection_name, limit=10000)
        existing_ids = {p.id for p in scroll.points if p.id is not None}
    except Exception as e:
        logger.warning(f"Không lấy được IDs hiện có: {e}")
    return existing_ids


def build_vectorstore(
    folder_path: str = "data",
    collection_name: str = "docs",
    host: str = "localhost",
    port: int = 6333,
) -> QdrantVectorStore:
    """
    Build hoặc thêm tài liệu mới vào vectorstore trong Qdrant với duplicate check.
    """
    # --- Khởi tạo embedder và client ---
    embeddings = get_embedder()
    client = QdrantClient(host=host, port=port)

    # --- Lấy dimension từ 1 embedding mẫu ---
    test_vector = embeddings.embed_query("dimension check")
    vector_size = len(test_vector)

    # --- Đảm bảo collection tồn tại ---
    ensure_collection_exists(client, collection_name, vector_size)

    # --- Load tài liệu ---
    logger.info(f"Đang load tài liệu từ: {folder_path}")
    docs = load_documents_from_folder(folder_path)
    if not docs:
        raise ValueError(f"Không tìm thấy tài liệu trong {folder_path}")

    # --- Chunk tài liệu ---
    chunks = chunk_documents(docs)
    if not chunks:
        raise ValueError("Chunking thất bại - không có chunk nào")
    logger.info(f"Đã split thành {len(chunks)} chunks")

    # --- Duplicate check ---
    existing_ids = get_existing_chunk_ids(client, collection_name)
    new_chunks = []
    for chunk in chunks:
        chunk_id = get_chunk_id(chunk.page_content)
        if chunk_id not in existing_ids:
            chunk.metadata["chunk_id"] = chunk_id
            new_chunks.append(chunk)

    # --- Thêm chunk mới vào vectorstore ---
    if new_chunks:
        QdrantVectorStore.from_documents(
            documents=new_chunks,
            embedding=embeddings,
            host=host,
            port=port,
            collection_name=collection_name,
        )
        logger.info(f"Đã thêm {len(new_chunks)} chunk mới vào collection '{collection_name}'")
    else:
        logger.info("Không có chunk mới để thêm.")

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

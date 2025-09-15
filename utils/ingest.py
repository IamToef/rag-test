# utils/ingest.py
import hashlib
import logging
from typing import Set, Optional, List

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.schema import Document

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
    try:
        collections = client.get_collections().collections
    except Exception as e:
        logger.warning(f"Không lấy được danh sách collection: {e}")
        collections = []

    if not any(c.name == collection_name for c in collections):
        logger.info(f"Tạo collection mới: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )
    else:
        logger.info(f"Collection '{collection_name}' đã tồn tại")

def get_existing_chunk_ids(client: QdrantClient, collection_name: str) -> Set[str]:
    """
    Lấy set ID của các chunk đã có trong collection.
    Thực hiện robustly vì client.scroll() trả về kiểu khác nhau giữa các phiên bản.
    """
    existing_ids: Set[str] = set()
    try:
        resp = client.scroll(collection_name=collection_name, limit=10000, with_payload=False, with_vectors=False)

        # resp có thể là:
        # - tuple/list: (points, next_page)
        # - object có attribute 'points'
        # - list of points
        if isinstance(resp, (tuple, list)):
            points = resp[0]
        elif hasattr(resp, "points"):
            points = resp.points
        else:
            points = resp  # fallback

        for p in points:
            # p có thể là object (has attr id) hoặc dict
            pid = getattr(p, "id", None)
            if pid is None and isinstance(p, dict):
                pid = p.get("id")
            if pid is not None:
                existing_ids.add(str(pid))
    except Exception as e:
        logger.warning(f"Không lấy được IDs hiện có: {e}")
    return existing_ids


def build_vectorstore(
    folder_path: str = "data",
    collection_name: str = "docs",
    host: Optional[str] = None,
    port: Optional[int] = None,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> QdrantVectorStore:
    """
    Build hoặc thêm tài liệu mới vào vectorstore trong Qdrant với duplicate check.

    - Nếu `url` + `api_key` được cung cấp => kết nối Qdrant Cloud
    - Ngược lại => dùng host/port (local)
    """

    # 1. Khởi tạo embedder
    embeddings = get_embedder()

    # 2. Khởi tạo Qdrant client (cloud hoặc local)
    if url and api_key:
        logger.info("Kết nối Qdrant Cloud...")
        client = QdrantClient(url=url, api_key=api_key)
    else:
        host_val = host or "localhost"
        port_val = port or 6333
        logger.info(f"Kết nối Qdrant Local tại {host_val}:{port_val} ...")
        client = QdrantClient(host=host_val, port=port_val)

    # 3. Lấy dimension từ 1 embedding mẫu (để tạo collection nếu cần)
    test_vector = embeddings.embed_query("dimension check")
    vector_size = len(test_vector)

    # 4. Đảm bảo collection tồn tại
    ensure_collection_exists(client, collection_name, vector_size)

    # 5. Load tài liệu từ folder và chunk
    logger.info(f"Đang load tài liệu từ: {folder_path}")
    docs = load_documents_from_folder(folder_path)
    if not docs:
        raise ValueError(f"Không tìm thấy tài liệu trong {folder_path}")

    chunks = chunk_documents(docs)
    if not chunks:
        raise ValueError("Chunking thất bại - không có chunk nào")
    logger.info(f"Đã split thành {len(chunks)} chunks")

    # 6. Lấy IDs hiện có trong collection (nếu có)
    existing_ids = get_existing_chunk_ids(client, collection_name)
    logger.info(f"Đã có {len(existing_ids)} chunk trong collection '{collection_name}'")

    # 7. Tạo list chunk mới (unique) dựa trên chunk_id
    new_chunks: List[Document] = [
        chunk for chunk in chunks 
        if chunk.metadata.get("chunk_id") not in existing_ids
    ]

    logger.info(f"{len(new_chunks)} chunk mới sẽ được thêm vào collection")


    # 8. Tạo instance vectorstore với client đã khởi tạo
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    # 9. Thêm chunk mới bằng API của vectorstore (đảm bảo không gọi QdrantClient.__init__ sai tham số)
    if new_chunks:
        # add_documents sẽ tự embed và upsert đúng cách
        vectorstore.add_documents(new_chunks)
        logger.info(f"Đã thêm {len(new_chunks)} chunk mới vào collection '{collection_name}'")
    else:
        logger.info("Không có chunk mới để thêm.")

    return vectorstore

def remove_duplicates(client: QdrantClient, collection_name: str) -> None:
    """
    Xoá các chunk duplicate trong collection dựa trên nội dung (page_content).
    Giữ lại chunk đầu tiên, xoá những bản trùng nội dung.
    """
    seen_texts = set()
    duplicate_ids = []

    # Scroll qua toàn bộ points trong collection
    try:
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
    except Exception as e:
        logger.error(f"Không thể scroll collection '{collection_name}': {e}")
        return

    for p in points:
        payload = getattr(p, "payload", None)
        pid = getattr(p, "id", None)

        if not payload or not pid:
            continue

        text = payload.get("page_content")
        if text in seen_texts:
            duplicate_ids.append(pid)
        else:
            seen_texts.add(text)

    if duplicate_ids:
        client.delete(collection_name=collection_name, points_selector=duplicate_ids)
        logger.info(f"Đã xoá {len(duplicate_ids)} chunks duplicate trong collection '{collection_name}'")
    else:
        logger.info(f"Không tìm thấy duplicate trong collection '{collection_name}'")


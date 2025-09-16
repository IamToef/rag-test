import os
import argparse
from utils.ingest import build_vectorstore, remove_duplicates
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

if __name__ == "__main__":
    # Load biến môi trường từ .env
    load_dotenv()

    # --- Config mặc định (Cloud) ---
    folder = "data"
    collection = "docs"
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")

    # --- Flag CLI ---
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Xóa toàn bộ collection và tạo lại")
    args = parser.parse_args()

    # Kết nối client
    client = QdrantClient(url=url, api_key=api_key)

    if args.reset:
        print(f"Đang xóa toàn bộ collection '{collection}'...")
        client.delete_collection(collection)
        print("✅ Collection đã được xóa.")

    # Build vectorstore (sẽ tự tạo lại collection nếu chưa tồn tại)
    vectorstore = build_vectorstore(
        folder_path=folder,
        collection_name=collection,
        url=url,
        api_key=api_key,
    )

    # Xoá vector trùng lặp (nếu có)
    remove_duplicates(vectorstore.client, collection)

    # Lấy thông tin collection để biết số lượng vector hiện tại
    info: rest.CollectionInfo = vectorstore.client.get_collection(collection)
    print("=======================================")
    print(f"Vectorstore '{collection}' đã được tạo/cập nhật trên Qdrant Cloud!")
    print(f"Số lượng vector hiện có: {info.points_count}")
    print("=======================================")

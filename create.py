import argparse
import os
from utils.ingest import build_vectorstore, remove_duplicates
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load biến môi trường từ .env
    load_dotenv()

    parser = argparse.ArgumentParser(description="Tạo hoặc cập nhật Qdrant vectorstore")

    parser.add_argument("--folder", type=str, default="data", help="Thư mục chứa tài liệu")
    parser.add_argument("--collection", type=str, default="docs", help="Tên collection trong Qdrant")
    parser.add_argument("--cloud", action="store_true", help="Chạy với Qdrant Cloud thay vì local")

    # Local (fallback)
    parser.add_argument("--host", type=str, default=os.getenv("QDRANT_HOST", "qdrant_server"))
    parser.add_argument("--port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")))

    # Cloud
    parser.add_argument("--url", type=str, default=os.getenv("QDRANT_URL"))
    parser.add_argument("--api_key", type=str, default=os.getenv("QDRANT_API_KEY"))

    args = parser.parse_args()

    if args.cloud:
        # Cloud mode
        vectorstore = build_vectorstore(
            folder_path=args.folder,
            collection_name=args.collection,
            url=args.url,
            api_key=args.api_key,
        )
        remove_duplicates(vectorstore.client, "docs")
        print(f"Vectorstore '{args.collection}' đã được tạo/cập nhật trên cloud!")
    else:
        # Local mode
        vectorstore = build_vectorstore(
            folder_path=args.folder,
            collection_name=args.collection,
            host=args.host,
            port=args.port,
        )
        remove_duplicates(vectorstore.client, "docs")
        print(f"Vectorstore '{args.collection}' đã được tạo/cập nhật trên local!")

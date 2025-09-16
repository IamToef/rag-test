import time
import os
import argparse
from dotenv import load_dotenv
from utils.retrieval import get_vectorstore
from utils.qa import build_qa_chain

# Load biến môi trường từ .env
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run Terminal RAG App with Qdrant")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Chạy ở chế độ Qdrant Cloud. Nếu không truyền thì mặc định local."
    )
    args = parser.parse_args()

    collection_name = os.getenv("QDRANT_COLLECTION", "docs")
    use_cloud = args.cloud

    # Load vectorstore từ Qdrant
    print("Đang load vectorstore...")
    start_load = time.time()
    vectorstore = get_vectorstore(collection_name=collection_name, use_cloud=use_cloud)
    qa_chain = build_qa_chain(vectorstore)
    end_load = time.time()
    print(f"Vectorstore load trong {end_load - start_load:.2f} giây.")
    print(f"App running in {'cloud' if use_cloud else 'local'} mode\n")

    conversation = []

    while True:
        try:
            query = input("Bạn: ")
            if query.lower() in ["exit", "quit"]:
                print("Thoát chương trình.")
                break

            conversation.append({"role": "user", "content": query})

            start = time.time()
            result = qa_chain.invoke({"query": query})
            answer = result if isinstance(result, str) else result.get("result", "")
            end = time.time()

            conversation.append({"role": "assistant", "content": answer})

            print(f"AI: {answer} (trả lời trong {end - start:.2f}s)")

        except KeyboardInterrupt:
            print("\nThoát chương trình.")
            break

if __name__ == "__main__":
    main()

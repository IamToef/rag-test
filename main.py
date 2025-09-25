from utils.indexing import DataManager
from utils.graph import build_graph
from utils.config import get_llms
import time

def main():
    print ("=== Starting Chatbot ===")
    start_time = time.time()
    # Lấy vectorstore đã được index sẵn
    dm = DataManager("my_collection")
    llm = get_llms()
    graph = build_graph(llm, dm.vector_store)
    end_time = time.time()
    print(f"=== Chatbot ready! (⏱ Load time: {end_time - start_time:.2f} seconds) ===")
    
    chat_history = []  # list để lưu lịch sử hội thoại

    print("=== Chatbot started (nhập 'exit' để thoát) ===")
    while True:
        question = input("You: ")
        if question.strip().lower() in ["exit"]:
            print("Chatbot: Bye 👋")
            break

        # Thêm lịch sử hội thoại vào input
        start = time.time()
        result = graph.invoke({
            "question": question,
            "chat_history": chat_history
        })
        end = time.time()

        print("Chatbot:", result["answer"])
        print(f"(⏱ Respond time: {end - start:.2f} seconds)")
        chat_history = result["chat_history"]  # cập nhật lịch sử hội thoại

if __name__ == "__main__":
    main()

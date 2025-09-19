from utils.agent import agent_executor
from utils.history import history, add_to_history
from utils.config import get_vector_store
import time

vector_store = get_vector_store("my_collection")

def run():
    config = {"configurable": {"thread_id": "def234"}}

    print("🤖 Chatbot đã sẵn sàng! Gõ 'exit' để thoát, 'clear' để xóa history, 'history' để xem lại.\n")
    while True:
        input_message = input("❓ Bạn: ").strip()
        if not input_message:
            continue

        # ---- COMMANDS ----
        if input_message.lower() in ["exit", "quit"]:
            print("👋 Tạm biệt!")
            break
        if input_message.lower() == "clear":
            history.clear()
            print("🧹 History đã được xóa!\n")
            continue
        if input_message.lower() == "history":
            print("\n📜 Lịch sử hội thoại:")
            for role, msg in history.get_messages():
                who = "👤 Bạn" if role == "user" else "🤖 Bot"
                print(f"{who}: {msg}")
            print()
            continue

        # ---- ADD USER MESSAGE ----
        add_to_history("user", input_message)

        # ---- RUN AGENT ----
        start = time.time()
        final_response = None
        for event in agent_executor.stream(
            {"messages": history.get_messages()},  # luôn truyền cả history cho agent
            stream_mode="values",
            config=config,
        ):
            final_response = event["messages"][-1].content
        end = time.time()

        # ---- ADD ASSISTANT MESSAGE ----
        if final_response:
            add_to_history("assistant", final_response)
            print("🤖 Bot:", final_response)

        print(f"⏱️ Time taken: {end - start:.2f} seconds\n")

if __name__ == "__main__":
    run()

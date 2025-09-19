import json
import os

HISTORY_FILE = "history.json"

class ChatHistory:
    def __init__(self):
        self.messages = []
        self.load_history()

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.save_history()

    def get_messages(self):
        return self.messages

    def save_history(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.messages = json.load(f)
        else:
            self.messages = []

    def clear(self):
        self.messages = []
        self.save_history()

# 🟢 khởi tạo 1 instance global
history = ChatHistory()

def add_to_history(role, content):
    history.add_message(role, content)

# utils/agent.py
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from utils.tools import retrieve
from utils.config import get_llms
from utils.history import ChatHistory

llm = get_llms()
memory = MemorySaver()
history = ChatHistory()

agent_executor = create_react_agent(
    llm,
    [retrieve],
    checkpointer=memory,
)

def add_to_history(role: str, content: str):
    """Hàm tiện ích để thêm message vào history"""
    if role == "user":
        history.add_user_message(content)
    elif role == "assistant":
        history.add_ai_message(content)

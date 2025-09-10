from langchain_ollama import OllamaEmbeddings
from .config import EMBEDDING_MODEL

def get_embedder():
    return OllamaEmbeddings(model=EMBEDDING_MODEL)

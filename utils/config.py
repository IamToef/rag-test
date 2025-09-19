import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import ChatOllama, OllamaEmbeddings

#from langchain.chat_models import init_chat_model

load_dotenv()

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["USER_AGENT"] = os.getenv("USER_AGENT", "ragtest/1.0 (https://example.com)")

def get_llms():
    llm = ChatOllama(
        model="mistral",
)
    return llm

def get_embeddings():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

def get_vector_store(collection_name="docs"):
    embeddings = get_embeddings()

    # In-memory Qdrant
    client = QdrantClient(#":memory"
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    vector_size = len(embeddings.embed_query("sample text"))

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    return vector_store

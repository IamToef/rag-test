import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_openai import ChatOpenAI
from huggingface_hub import InferenceClient
from langchain_core.embeddings import Embeddings

# Load biến môi trường
load_dotenv()

# LangSmith (tùy chọn, nếu bạn muốn tracking)
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["USER_AGENT"] = os.getenv("USER_AGENT", "ragtest/1.0 (https://example.com)")


# ----------------- LLM -----------------
def get_llms():
    llm = ChatOpenAI(
        model="gpt-4.1-mini",   # hoặc "gpt-4o-mini" tùy bạn muốn loại nào
        temperature=0,          # chỉnh độ sáng tạo (0 = chính xác, >0 = sáng tạo hơn)
        api_key=os.getenv("OPENAI_API_KEY")  # key bạn đã có sẵn
    )
    return llm
# ----------------- Embeddings -----------------
class HuggingFaceEmbeddings(Embeddings):
    """Wrapper cho HF Inference API để dùng làm embeddings trong LangChain."""

    def __init__(self, model="google/embeddinggemma-300m", token=None):
        self.client = InferenceClient(
            model=model,
            token=token or os.environ.get("HF_TOKEN")
        )

    def embed_query(self, text: str):
        """Trả về embedding cho một câu query"""
        return self.client.feature_extraction(text)

    def embed_documents(self, texts: list[str]):
        """Trả về embeddings cho nhiều documents"""
        return [self.client.feature_extraction(t) for t in texts]


def get_embeddings():
    """Khởi tạo HuggingFaceEmbeddings"""
    return HuggingFaceEmbeddings()


# ----------------- Vector Store -----------------
def get_vector_store(collection_name="my_collection"):
    embeddings = get_embeddings()

    # Kết nối Qdrant
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    # Lấy chiều của vector từ model embedding
    vector_size = len(embeddings.embed_query("sample text"))

    # Tạo collection nếu chưa có
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            ),
        )

    # Tạo QdrantVectorStore
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    return vector_store

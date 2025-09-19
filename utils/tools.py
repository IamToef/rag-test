from langchain_core.tools import tool
from utils.config import get_vector_store

# 👉 Chỉ kết nối tới vector store có sẵn
vector_store = get_vector_store("my_collection")

@tool(response_format="content_and_artifact")
def retrieve(query: str, **kwargs):
    """Retrieve information related to a query."""
    threshold = kwargs.get("threshold", 0.7)  # default 0.7
    k = kwargs.get("k", 4)

    results = vector_store.similarity_search_with_relevance_scores(
        query, k=k, threshold=threshold
    )

    serialized_parts = []
    for idx, (doc, score) in enumerate(results, start=1):
        snippet = doc.page_content[:200] + ("..." if len(doc.page_content) > 200 else "")
        vector_id = doc.metadata.get("id", "N/A")
        serialized_parts.append(
            f"K={idx}, Score={score:.4f}, ID={vector_id}\nSnippet: {snippet}"
        )
    serialized = "\n\n".join(serialized_parts)
    return serialized, results

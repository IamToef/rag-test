from utils.schema import Search, State
from langchain_core.prompts import PromptTemplate

template = """Answer everything in Vietnamese. Use the provided pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.

{context}

Question: {question}

Helpful Answer:"""
prompt = PromptTemplate.from_template(template)

def analyze_query(state: State, llm):
    structured_llm = llm.with_structured_output(Search)
    query = structured_llm.invoke(state["question"])
    return {"query": query}

def retrieve(state: State, vector_store, k: int = 10):
    query = state["query"]

    # Lấy nhiều kết quả (vd: k=10)
    results = vector_store.similarity_search_with_score(query["query"], k=k)

    # Sắp xếp theo distance tăng dần (gần nhất trước)
    results = sorted(results, key=lambda x: x[1])

    print(f"\n🔎 Top 3 kết quả gần nhất cho query: '{query['query']}'")
    for i, (doc, distance) in enumerate(results[:3], start=1):
        print(f"{i}. Page: {doc.metadata.get('page', 'N/A')}, "
              f"ID: {doc.metadata.get('_id', 'N/A')}, "
              f"Source: {doc.metadata.get('source', 'N/A')}"
              f", Distance: {distance:.4f}")

    # vẫn trả về toàn bộ k docs cho pipeline
    retrieved_docs = []
    for doc, distance in results:
        doc.metadata["distance"] = distance
        retrieved_docs.append(doc)

    return {"context": retrieved_docs}


def generate(state: State, llm):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    
    history= state.get("chat_history", [])
    history_str = ""
    for role, content in history:
        history_str += f"{role}: {content}\n"

    messages = prompt.invoke({
        "question": state["question"], 
        "context": f"{history_str}\n{docs_content}"
    })
    
    response = llm.invoke(messages)

    new_history = history + [("user", state["question"]), ("assistant", response.content)]
    return {
        "answer": response.content,
        "chat_history": new_history
    }
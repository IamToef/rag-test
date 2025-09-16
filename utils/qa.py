from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM
from .config import LANGUAGE_MODEL
from .prompt import VIETNAMESE_PROMPT

def build_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_kwargs={
        "k": 5,
        "score_threshold": 0.7})
    llm = OllamaLLM(model=LANGUAGE_MODEL)
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": VIETNAMESE_PROMPT}
    )


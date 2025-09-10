import os
from langchain_community.vectorstores import FAISS
from .embedder import get_embedder
from .chunker import chunk_documents
from .loader import load_documents_from_folder
from .config import PERSIST_DIR

def build_vectorstore(folder_path="data", refresh=False):
    """
    Build hoặc load vectorstore từ folder chứa tài liệu hướng dẫn
    
    Args:
        folder_path (str): Đường dẫn tới thư mục chứa tài liệu
        refresh (bool): Force rebuild vectorstore nếu True
    Returns:
        FAISS: Vectorstore đã build/load
    """
    # Kiểm tra và load vectorstore có sẵn
    if not refresh and os.path.exists(PERSIST_DIR):
        index_path = os.path.join(PERSIST_DIR, "index.faiss")
        if os.path.exists(index_path):
            print(f"Loading existing vectorstore from {PERSIST_DIR}")
            return FAISS.load_local(
                PERSIST_DIR, 
                get_embedder(), 
                allow_dangerous_deserialization=True
            )

    # Build vectorstore mới
    print(f"Building new vectorstore from: {folder_path}")
    
    # Load và chunk documents
    docs = load_documents_from_folder(folder_path)
    if not docs:
        raise ValueError(f"No documents found in {folder_path}")
        
    print(f"Loaded {len(docs)} documents")
    
    # Chunk documents theo strategy cho tài liệu hướng dẫn
    chunks = chunk_documents(docs)
    if not chunks:
        raise ValueError("Chunking failed - no chunks generated")
    
    print(f"Split into {len(chunks)} chunks")

    # Build vectorstore
    try:
        embeddings = get_embedder()
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # Lưu vectorstore
        os.makedirs(PERSIST_DIR, exist_ok=True)
        vectorstore.save_local(PERSIST_DIR)
        print(f"Vectorstore built and saved at {PERSIST_DIR}")
        
        return vectorstore
        
    except Exception as e:
        print(f"Error building vectorstore: {str(e)}")
        raise
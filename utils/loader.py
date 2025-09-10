import os
from typing import List
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader, 
    UnstructuredExcelLoader,
    PDFMinerLoader
)

class DocumentLoader:
    def __init__(self):
        self.loader_mapping = {
            '.txt': TextLoader,
            '.csv': CSVLoader,
            '.doc': UnstructuredWordDocumentLoader,
            '.docx': UnstructuredWordDocumentLoader,
            '.ppt': UnstructuredPowerPointLoader,
            '.pptx': UnstructuredPowerPointLoader,
            '.xls': UnstructuredExcelLoader,
            '.xlsx': UnstructuredExcelLoader,
            '.pdf': PDFMinerLoader
        }

    def get_loader_for_file(self, file_path: str):
        """Return appropriate loader based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.loader_mapping:
            raise ValueError(f"Unsupported file type: {ext}")
        return self.loader_mapping[ext]

    def load_documents_from_folder(self, folder_path: str) -> List[Document]:
        """Load documents from folder"""
        documents = []
        
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            
            try:
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                    
                # Get appropriate loader
                loader_class = self.get_loader_for_file(file_path)
                loader = loader_class(file_path)
                
                # Load documents
                docs = loader.load()
                
                # Add base metadata
                for doc in docs:
                    doc.metadata.update({
                        "source": file,
                        "file_type": os.path.splitext(file)[1],
                        "content_type": "text"
                    })
                
                documents.extend(docs)
                print(f"Loaded {len(docs)} documents from {file}")
                
            except Exception as e:
                print(f"Error loading {file}: {str(e)}")
                continue
                
        return documents

# Create singleton instance
document_loader = DocumentLoader()

# Export the load_documents_from_folder function
def load_documents_from_folder(folder_path: str) -> List[Document]:
    return document_loader.load_documents_from_folder(folder_path)
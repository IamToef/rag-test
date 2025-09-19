# load_data.py
import os
import hashlib
import json
import bs4
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    WebBaseLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.config import get_vector_store


class DataManager:
    def __init__(self, collection_name: str = "default", hash_file: str = "data_hash.json"):
        """
        Initialize DataManager with a vector store collection (persistent Qdrant).
        """
        self.collection_name = collection_name
        self.vector_store = get_vector_store(collection_name=collection_name)
        self.hash_file = hash_file
        self._data_hash = None

        # Load previous hash if exists
        if os.path.exists(self.hash_file):
            try:
                with open(self.hash_file, "r") as f:
                    self._data_hash = json.load(f).get("hash")
            except Exception:
                self._data_hash = None

    def reset(self):
        """
        Clear all documents from the vector store.
        """
        if hasattr(self.vector_store, "delete_collection"):
            self.vector_store.delete_collection()
            print(f"🗑️ Vector store '{self.collection_name}' has been reset.")
            self.vector_store = get_vector_store(collection_name=self.collection_name)
        else:
            if hasattr(self.vector_store, "_vectors"):
                self.vector_store._vectors.clear()
            print(f"🗑️ Vector store '{self.collection_name}' cleared (in-memory fallback).")

    def _compute_data_hash(self, folder_path=None, web_urls=None):
        """
        Compute a hash based on file names, sizes, and web URLs.
        Used to detect changes for smart reload.
        """
        m = hashlib.md5()
        # Folder files
        if folder_path and os.path.exists(folder_path):
            for root, _, files in os.walk(folder_path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        m.update(file.encode())
                        m.update(str(stat.st_mtime).encode())
                        m.update(str(stat.st_size).encode())
                    except Exception:
                        continue
        # Web URLs
        if web_urls:
            for url in sorted(web_urls):
                m.update(url.encode())
        return m.hexdigest()

    def _save_hash(self):
        """
        Save the current _data_hash to file for persistence.
        """
        try:
            with open(self.hash_file, "w") as f:
                json.dump({"hash": self._data_hash}, f)
        except Exception as e:
            print(f"⚠️ Failed to save hash file: {e}")

    def smart_reload(self, folder_path=None, web_urls=None, **kwargs):
        new_hash = self._compute_data_hash(folder_path, web_urls)
        if self._data_hash != new_hash:
            print("🔄 Changes detected. Resetting and reloading vector store...")
            self.reset()
            self.load_and_index(
                folder_path=folder_path,
                **kwargs
            )
            self._data_hash = new_hash
            self._save_hash()
            print("✅ Smart reload complete!")
        else:
            print("ℹ️ No changes detected. Vector store is up-to-date.")

    def load_and_index(
        self,
        folder_path: str = None,
        web_urls: list[str] = None,
        chunk_size: int = 1536,
        chunk_overlap: int = 536
    ):
        """
        Load documents from folder and/or web, chunk them, and add to vector store.
        Supports .pdf, .docx, .txt, .md files and web URLs.
        """
        docs = []

        # ----- FOLDER LOADING -----
        if folder_path:
            folder_path = folder_path.strip()
            if not os.path.exists(folder_path):
                print(f"⚠️ Folder path does not exist: {folder_path}")
            else:
                print(f"📂 Scanning folder: {folder_path}")
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_clean = file.strip()
                        file_path = os.path.join(root, file_clean)
                        ext = file_clean.lower().split(".")[-1]
                        loader = None

                        if ext == "pdf":
                            loader = PyPDFLoader(file_path)
                        elif ext == "docx":
                            loader = Docx2txtLoader(file_path)
                        elif ext in ("txt", "md"):
                            loader = TextLoader(file_path)
                        else:
                            print(f"⚠️ Skipping unsupported file type: {file_clean}")
                            continue

                        try:
                            file_docs = loader.load()
                            print(f"✅ Loaded {len(file_docs)} docs from {file_clean}")
                            docs.extend(file_docs)
                        except Exception as e:
                            print(f"⚠️ Failed to load {file_clean}: {e}")

        # ----- WEB LOADING -----
        if web_urls:
            for url in web_urls:
                try:
                    loader = WebBaseLoader(url)
                    url_docs = loader.load()
                    print(f"🌐 Loaded {len(url_docs)} docs from {url}")
                    docs.extend(url_docs)
                except Exception as e:
                    print(f"⚠️ Failed to load {url}: {e}")

        # ----- CHUNKING -----
        if not docs:
            print("⚠️ No documents loaded. Nothing to index.")
            return self.vector_store

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        all_splits = text_splitter.split_documents(docs)
        print(f"Chunked into {len(all_splits)} pieces")

        # ----- INDEXING -----
        _ = self.vector_store.add_documents(documents=all_splits)
        print(f"Indexed {len(all_splits)} chunks into vector store")

        return self.vector_store


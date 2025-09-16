# Model config
EMBEDDING_MODEL = "toshk0/nomic-embed-text-v2-moe:Q6_K"   # hoặc model embed từ Ollama
LANGUAGE_MODEL = "mistral"              # Ollama LLM model

# Vectorstore config
PERSIST_DIR = "vectorstores"

# Chunk config
CHUNK_SIZE = 1536
CHUNK_OVERLAP = 536

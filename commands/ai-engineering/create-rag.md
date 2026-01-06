---
name: create-rag
description: Generate RAG (Retrieval-Augmented Generation) application boilerplate
agent: rag-specialist
arguments:
  - name: name
    description: Name of the RAG application
    required: true
  - name: vectordb
    description: "Vector database to use (chromadb, qdrant, weaviate, pgvector, pinecone)"
    required: false
    default: chromadb
  - name: framework
    description: "Framework to use (llamaindex, langchain)"
    required: false
    default: langchain
---

# Create RAG Application

Generate a complete RAG application structure with your choice of vector database and framework.

## Usage

```
/create-rag my-knowledge-base
/create-rag my-rag --vectordb qdrant --framework llamaindex
```

## What Gets Created

```
{name}/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── embeddings.py       # Embedding model setup
│   ├── vectorstore.py      # Vector database connection
│   ├── ingestion.py        # Document loading and chunking
│   ├── retriever.py        # Retrieval logic
│   └── chain.py            # RAG chain implementation
├── scripts/
│   ├── ingest.py           # Bulk ingestion script
│   └── query.py            # Interactive query script
├── tests/
│   └── test_rag.py         # Basic tests
├── data/
│   └── .gitkeep            # Document storage
├── requirements.txt
├── .env.example
└── README.md
```

## Vector Database Options

| Option | Best For |
|--------|----------|
| `chromadb` | Local development, prototyping |
| `qdrant` | Production, advanced filtering |
| `weaviate` | Hybrid search (vector + keyword) |
| `pgvector` | Existing PostgreSQL users |
| `pinecone` | Managed, serverless |

## Framework Options

| Option | Features |
|--------|----------|
| `langchain` | Flexible chains, many integrations |
| `llamaindex` | Document-focused, easy indexing |

## Agent Assignment

This command uses the **rag-specialist** agent.

## Example Generated Code

### config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Embedding
    embedding_model: str = "text-embedding-3-small"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    top_k: int = 5

    # Vector DB
    vectordb_url: str = "http://localhost:6333"
    collection_name: str = "documents"

    class Config:
        env_file = ".env"
```

### retriever.py
```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

def create_hybrid_retriever(vectorstore, documents):
    """Create hybrid retriever combining vector and keyword search"""
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    bm25_retriever = BM25Retriever.from_documents(documents)

    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.3, 0.7]
    )
```

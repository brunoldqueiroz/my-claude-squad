"""Semantic memory with vector embeddings for similarity search.

This module provides semantic search capabilities on top of the key-value memory.
It uses sentence-transformers for embedding generation and cosine similarity for search.

Installation:
    uv sync --extra semantic

Usage:
    from orchestrator.semantic_memory import SemanticMemory, is_available

    if is_available():
        memory = SemanticMemory()
        memory.store_semantic("key1", "The quick brown fox", namespace="docs")
        results = memory.search_semantic("fast animal", top_k=5)
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Check if sentence-transformers is available
_SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None  # type: ignore
    np = None  # type: ignore


def is_available() -> bool:
    """Check if semantic memory is available (sentence-transformers installed).

    Returns:
        True if semantic memory can be used, False otherwise
    """
    return _SENTENCE_TRANSFORMERS_AVAILABLE


@dataclass
class SemanticSearchResult:
    """Result from semantic search.

    Attributes:
        key: Memory key
        value: Memory value
        namespace: Memory namespace
        similarity: Cosine similarity score (0-1, higher is more similar)
        metadata: Optional metadata dict
        created_at: When the memory was created
    """
    key: str
    value: str
    namespace: str
    similarity: float
    metadata: dict[str, Any]
    created_at: datetime


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider using sentence-transformers.

    Uses the all-MiniLM-L6-v2 model by default (~80MB, 384 dimensions).
    This model provides a good balance of speed and quality.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str | None = None):
        """Initialize the provider.

        Args:
            model_name: Model to use. Defaults to all-MiniLM-L6-v2

        Raises:
            ImportError: If sentence-transformers is not installed
        """
        if not _SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for semantic memory. "
                "Install with: uv sync --extra semantic"
            )

        self._model_name = model_name or self.DEFAULT_MODEL
        self._model: SentenceTransformer | None = None
        self._dimension: int | None = None

    def _load_model(self) -> SentenceTransformer:
        """Lazy load the model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Dimension: {self._dimension}")
        return self._model

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if self._dimension is None:
            self._load_model()
        return self._dimension  # type: ignore

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        model = self._load_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity (0-1, higher is more similar)
    """
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        # Fallback pure Python implementation
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    # Use numpy for efficiency
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


class SemanticMemory:
    """Memory with semantic search capabilities.

    Extends the key-value memory with vector embeddings for similarity-based
    retrieval. Stores embeddings alongside memories in DuckDB.

    Example:
        memory = SemanticMemory()

        # Store with embedding
        memory.store_semantic("doc1", "Python is a programming language", namespace="docs")
        memory.store_semantic("doc2", "JavaScript runs in browsers", namespace="docs")

        # Search by meaning
        results = memory.search_semantic("coding languages", namespace="docs", top_k=2)
        for result in results:
            print(f"{result.key}: {result.similarity:.2f}")
    """

    def __init__(
        self,
        db_path: Path | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        """Initialize semantic memory.

        Args:
            db_path: Path to DuckDB database. Defaults to .swarm/memory.duckdb
            embedding_provider: Provider for generating embeddings.
                               Defaults to SentenceTransformerProvider.

        Raises:
            ImportError: If semantic dependencies are not available
        """
        if not _SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers and numpy are required for semantic memory. "
                "Install with: uv sync --extra semantic"
            )

        import duckdb

        if db_path is None:
            swarm_dir = Path(__file__).parent.parent / ".swarm"
            swarm_dir.mkdir(exist_ok=True)
            db_path = swarm_dir / "memory.duckdb"

        self.db_path = db_path
        self.conn = duckdb.connect(str(db_path))
        self._provider = embedding_provider or SentenceTransformerProvider()
        self._init_tables()

    def _init_tables(self) -> None:
        """Initialize embedding tables."""
        # Create embeddings table if it doesn't exist
        # Store embeddings as JSON array of floats
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_embeddings (
                key VARCHAR PRIMARY KEY,
                embedding JSON NOT NULL,
                model VARCHAR NOT NULL,
                dimension INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster lookups
        try:
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_key
                ON memory_embeddings(key)
            """)
        except Exception:
            pass  # Index might already exist

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._provider.dimension

    def store_semantic(
        self,
        key: str,
        value: str,
        namespace: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a memory with its embedding.

        Stores both the key-value pair and its vector embedding.

        Args:
            key: Unique key
            value: Value to store (this is what gets embedded)
            namespace: Optional namespace for organization
            metadata: Optional metadata dict
        """
        # Store in main memories table
        metadata_json = json.dumps(metadata or {})
        self.conn.execute(
            """
            INSERT OR REPLACE INTO memories (key, value, namespace, metadata, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [key, value, namespace, metadata_json],
        )

        # Generate and store embedding
        embedding = self._provider.embed(value)
        embedding_json = json.dumps(embedding)

        self.conn.execute(
            """
            INSERT OR REPLACE INTO memory_embeddings
            (key, embedding, model, dimension, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [key, embedding_json, "sentence-transformers", len(embedding)],
        )

        logger.debug(f"Stored semantic memory: {key}")

    def store_semantic_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = "default",
    ) -> int:
        """Store multiple memories with embeddings efficiently.

        Args:
            items: List of dicts with 'key', 'value', and optional 'metadata'
            namespace: Namespace for all items

        Returns:
            Number of items stored
        """
        if not items:
            return 0

        # Extract texts for batch embedding
        texts = [item["value"] for item in items]
        embeddings = self._provider.embed_batch(texts)

        for item, embedding in zip(items, embeddings):
            key = item["key"]
            value = item["value"]
            metadata = item.get("metadata", {})

            metadata_json = json.dumps(metadata)
            embedding_json = json.dumps(embedding)

            self.conn.execute(
                """
                INSERT OR REPLACE INTO memories (key, value, namespace, metadata, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [key, value, namespace, metadata_json],
            )

            self.conn.execute(
                """
                INSERT OR REPLACE INTO memory_embeddings
                (key, embedding, model, dimension, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [key, embedding_json, "sentence-transformers", len(embedding)],
            )

        logger.info(f"Stored {len(items)} semantic memories in batch")
        return len(items)

    def search_semantic(
        self,
        query: str,
        namespace: str | None = None,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list[SemanticSearchResult]:
        """Search memories by semantic similarity.

        Args:
            query: Search query text
            namespace: Optional namespace to search within
            top_k: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of SemanticSearchResult sorted by similarity (highest first)
        """
        # Generate query embedding
        query_embedding = self._provider.embed(query)

        # Get all memories with embeddings
        sql = """
            SELECT m.key, m.value, m.namespace, m.metadata, m.created_at, e.embedding
            FROM memories m
            INNER JOIN memory_embeddings e ON m.key = e.key
        """
        params: list[Any] = []

        if namespace:
            sql += " WHERE m.namespace = ?"
            params.append(namespace)

        rows = self.conn.execute(sql, params).fetchall()

        # Calculate similarities
        results: list[tuple[SemanticSearchResult, float]] = []

        for row in rows:
            key, value, ns, metadata_json, created_at, embedding_json = row
            embedding = json.loads(embedding_json)

            similarity = cosine_similarity(query_embedding, embedding)

            if similarity >= min_similarity:
                metadata = json.loads(metadata_json) if metadata_json else {}
                result = SemanticSearchResult(
                    key=key,
                    value=value,
                    namespace=ns,
                    similarity=similarity,
                    metadata=metadata,
                    created_at=created_at,
                )
                results.append((result, similarity))

        # Sort by similarity (descending) and take top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in results[:top_k]]

    def get_embedding(self, key: str) -> list[float] | None:
        """Get the embedding for a specific memory.

        Args:
            key: Memory key

        Returns:
            Embedding vector or None if not found
        """
        result = self.conn.execute(
            "SELECT embedding FROM memory_embeddings WHERE key = ?",
            [key],
        ).fetchone()

        if result:
            return json.loads(result[0])
        return None

    def has_embedding(self, key: str) -> bool:
        """Check if a memory has an embedding.

        Args:
            key: Memory key

        Returns:
            True if embedding exists
        """
        result = self.conn.execute(
            "SELECT 1 FROM memory_embeddings WHERE key = ?",
            [key],
        ).fetchone()
        return result is not None

    def delete_embedding(self, key: str) -> bool:
        """Delete an embedding.

        Args:
            key: Memory key

        Returns:
            True if deleted, False if not found
        """
        result = self.conn.execute(
            "DELETE FROM memory_embeddings WHERE key = ? RETURNING key",
            [key],
        ).fetchone()
        return result is not None

    def delete_semantic(self, key: str) -> bool:
        """Delete both memory and its embedding.

        Args:
            key: Memory key

        Returns:
            True if deleted, False if not found
        """
        # Delete embedding
        self.conn.execute("DELETE FROM memory_embeddings WHERE key = ?", [key])

        # Delete memory
        result = self.conn.execute(
            "DELETE FROM memories WHERE key = ? RETURNING key",
            [key],
        ).fetchone()

        return result is not None

    def reindex_all(self) -> int:
        """Regenerate embeddings for all memories.

        Useful after changing the embedding model.

        Returns:
            Number of memories reindexed
        """
        # Get all memories
        rows = self.conn.execute(
            "SELECT key, value FROM memories"
        ).fetchall()

        if not rows:
            return 0

        # Batch embed all values
        keys = [row[0] for row in rows]
        values = [row[1] for row in rows]
        embeddings = self._provider.embed_batch(values)

        # Update embeddings
        for key, embedding in zip(keys, embeddings):
            embedding_json = json.dumps(embedding)
            self.conn.execute(
                """
                INSERT OR REPLACE INTO memory_embeddings
                (key, embedding, model, dimension, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [key, embedding_json, "sentence-transformers", len(embedding)],
            )

        logger.info(f"Reindexed {len(rows)} memories")
        return len(rows)

    def get_stats(self) -> dict[str, Any]:
        """Get semantic memory statistics.

        Returns:
            Dict with memory and embedding counts
        """
        memory_count = self.conn.execute(
            "SELECT COUNT(*) FROM memories"
        ).fetchone()[0]

        embedding_count = self.conn.execute(
            "SELECT COUNT(*) FROM memory_embeddings"
        ).fetchone()[0]

        # Get embeddings by namespace
        namespace_stats = self.conn.execute("""
            SELECT m.namespace, COUNT(*) as count
            FROM memories m
            INNER JOIN memory_embeddings e ON m.key = e.key
            GROUP BY m.namespace
        """).fetchall()

        return {
            "total_memories": memory_count,
            "memories_with_embeddings": embedding_count,
            "embedding_dimension": self.dimension,
            "embedding_model": "sentence-transformers",
            "by_namespace": {ns: count for ns, count in namespace_stats},
        }

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()


# Singleton instance
_semantic_memory: SemanticMemory | None = None


def get_semantic_memory() -> SemanticMemory | None:
    """Get or create the singleton SemanticMemory instance.

    Returns None if semantic memory is not available (dependencies not installed).

    Returns:
        The global SemanticMemory instance or None
    """
    global _semantic_memory

    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        return None

    if _semantic_memory is None:
        try:
            _semantic_memory = SemanticMemory()
        except Exception as e:
            logger.warning(f"Failed to initialize semantic memory: {e}")
            return None

    return _semantic_memory

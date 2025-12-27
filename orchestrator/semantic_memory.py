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

# Check if hnswlib is available for ANN
_HNSWLIB_AVAILABLE = False
try:
    import hnswlib
    _HNSWLIB_AVAILABLE = True
except ImportError:
    hnswlib = None  # type: ignore


def is_available() -> bool:
    """Check if semantic memory is available (sentence-transformers installed).

    Returns:
        True if semantic memory can be used, False otherwise
    """
    return _SENTENCE_TRANSFORMERS_AVAILABLE


def is_ann_available() -> bool:
    """Check if ANN (Approximate Nearest Neighbor) is available.

    ANN provides much faster similarity search for large datasets (>10K memories).
    Requires hnswlib to be installed.

    Returns:
        True if ANN can be used, False otherwise
    """
    return _HNSWLIB_AVAILABLE and _SENTENCE_TRANSFORMERS_AVAILABLE


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


class HNSWIndex:
    """HNSW-based Approximate Nearest Neighbor index.

    Uses hnswlib for fast similarity search on large datasets.
    Provides O(log n) search time instead of O(n) brute force.

    Example:
        index = HNSWIndex(dimension=384)
        index.add_items(keys, embeddings)
        neighbors = index.search(query_embedding, k=5)
    """

    def __init__(
        self,
        dimension: int,
        max_elements: int = 100000,
        ef_construction: int = 200,
        M: int = 16,
        space: str = "cosine",
    ):
        """Initialize HNSW index.

        Args:
            dimension: Embedding dimension
            max_elements: Maximum number of elements (can be extended)
            ef_construction: Construction time/accuracy trade-off (higher = better quality)
            M: Number of bi-directional links (higher = better quality, more memory)
            space: Distance metric ('cosine', 'l2', 'ip')

        Raises:
            ImportError: If hnswlib is not installed
        """
        if not _HNSWLIB_AVAILABLE:
            raise ImportError(
                "hnswlib is required for ANN search. "
                "Install with: uv sync --extra ann"
            )

        self.dimension = dimension
        self.max_elements = max_elements
        self.space = space

        # Create the index
        self._index = hnswlib.Index(space=space, dim=dimension)
        self._index.init_index(
            max_elements=max_elements,
            ef_construction=ef_construction,
            M=M,
        )

        # Key mapping: internal ID -> key
        self._id_to_key: dict[int, str] = {}
        self._key_to_id: dict[str, int] = {}
        self._next_id: int = 0

        logger.info(f"Initialized HNSW index: dim={dimension}, max={max_elements}")

    @property
    def count(self) -> int:
        """Return the number of elements in the index."""
        return len(self._id_to_key)

    def add_item(self, key: str, embedding: list[float]) -> None:
        """Add a single item to the index.

        Args:
            key: Unique identifier for this embedding
            embedding: Vector embedding
        """
        if key in self._key_to_id:
            # Update existing item
            item_id = self._key_to_id[key]
        else:
            # New item
            item_id = self._next_id
            self._next_id += 1

            # Resize if needed
            if item_id >= self.max_elements:
                new_max = self.max_elements * 2
                self._index.resize_index(new_max)
                self.max_elements = new_max
                logger.info(f"Resized HNSW index to {new_max} elements")

        self._id_to_key[item_id] = key
        self._key_to_id[key] = item_id

        # Add to index
        embedding_arr = np.array([embedding], dtype=np.float32)
        self._index.add_items(embedding_arr, np.array([item_id]))

    def add_items(self, keys: list[str], embeddings: list[list[float]]) -> None:
        """Add multiple items to the index efficiently.

        Args:
            keys: List of unique identifiers
            embeddings: List of vector embeddings
        """
        if not keys:
            return

        # Prepare IDs
        ids = []
        for key in keys:
            if key in self._key_to_id:
                item_id = self._key_to_id[key]
            else:
                item_id = self._next_id
                self._next_id += 1
            ids.append(item_id)
            self._id_to_key[item_id] = key
            self._key_to_id[key] = item_id

        # Resize if needed
        max_id = max(ids) + 1
        if max_id > self.max_elements:
            new_max = max(max_id * 2, self.max_elements * 2)
            self._index.resize_index(new_max)
            self.max_elements = new_max
            logger.info(f"Resized HNSW index to {new_max} elements")

        # Add to index
        embeddings_arr = np.array(embeddings, dtype=np.float32)
        self._index.add_items(embeddings_arr, np.array(ids))

        logger.debug(f"Added {len(keys)} items to HNSW index")

    def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        ef_search: int = 50,
    ) -> list[tuple[str, float]]:
        """Search for nearest neighbors.

        Args:
            query_embedding: Query vector
            k: Number of neighbors to return
            ef_search: Search time/accuracy trade-off (higher = more accurate)

        Returns:
            List of (key, similarity) tuples, sorted by similarity descending
        """
        if self.count == 0:
            return []

        # Adjust k if we have fewer items
        k = min(k, self.count)

        # Set search parameters
        self._index.set_ef(ef_search)

        # Search
        query_arr = np.array([query_embedding], dtype=np.float32)
        labels, distances = self._index.knn_query(query_arr, k=k)

        # Convert to (key, similarity) tuples
        # For cosine space, distance = 1 - similarity
        results = []
        for label, distance in zip(labels[0], distances[0]):
            if label in self._id_to_key:
                key = self._id_to_key[label]
                similarity = 1.0 - distance if self.space == "cosine" else 1.0 / (1.0 + distance)
                results.append((key, float(similarity)))

        return results

    def remove_item(self, key: str) -> bool:
        """Remove an item from the index.

        Note: hnswlib doesn't support true deletion, so we just remove from mappings.
        The vector remains but won't be returned in searches.

        Args:
            key: Key to remove

        Returns:
            True if removed, False if not found
        """
        if key not in self._key_to_id:
            return False

        item_id = self._key_to_id[key]
        del self._key_to_id[key]
        del self._id_to_key[item_id]
        return True

    def save(self, path: Path) -> None:
        """Save the index to disk.

        Args:
            path: File path to save to
        """
        self._index.save_index(str(path))

        # Save mappings
        mappings = {
            "id_to_key": self._id_to_key,
            "key_to_id": self._key_to_id,
            "next_id": self._next_id,
            "dimension": self.dimension,
            "max_elements": self.max_elements,
            "space": self.space,
        }
        mappings_path = path.with_suffix(".mappings.json")
        mappings_path.write_text(json.dumps(mappings))

        logger.info(f"Saved HNSW index to {path}")

    @classmethod
    def load(cls, path: Path) -> "HNSWIndex":
        """Load an index from disk.

        Args:
            path: File path to load from

        Returns:
            Loaded HNSWIndex
        """
        if not _HNSWLIB_AVAILABLE:
            raise ImportError("hnswlib is required to load HNSW index")

        # Load mappings
        mappings_path = path.with_suffix(".mappings.json")
        mappings = json.loads(mappings_path.read_text())

        # Create index
        instance = cls(
            dimension=mappings["dimension"],
            max_elements=mappings["max_elements"],
            space=mappings["space"],
        )

        # Load index data
        instance._index.load_index(str(path), max_elements=mappings["max_elements"])

        # Restore mappings (convert string keys back to int for id_to_key)
        instance._id_to_key = {int(k): v for k, v in mappings["id_to_key"].items()}
        instance._key_to_id = mappings["key_to_id"]
        instance._next_id = mappings["next_id"]

        logger.info(f"Loaded HNSW index from {path} ({instance.count} items)")
        return instance


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

    Supports optional ANN (Approximate Nearest Neighbor) for fast search on
    large datasets. Enable with use_ann=True (requires hnswlib).

    Example:
        memory = SemanticMemory()

        # Store with embedding
        memory.store_semantic("doc1", "Python is a programming language", namespace="docs")
        memory.store_semantic("doc2", "JavaScript runs in browsers", namespace="docs")

        # Search by meaning
        results = memory.search_semantic("coding languages", namespace="docs", top_k=2)
        for result in results:
            print(f"{result.key}: {result.similarity:.2f}")

        # With ANN for large datasets
        memory_ann = SemanticMemory(use_ann=True)
        memory_ann.build_ann_index()  # Build index from existing embeddings
    """

    def __init__(
        self,
        db_path: Path | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        use_ann: bool = False,
        ann_threshold: int = 1000,
    ):
        """Initialize semantic memory.

        Args:
            db_path: Path to DuckDB database. Defaults to .swarm/memory.duckdb
            embedding_provider: Provider for generating embeddings.
                               Defaults to SentenceTransformerProvider.
            use_ann: Enable ANN for fast similarity search (requires hnswlib)
            ann_threshold: Minimum memories before using ANN (default 1000)

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
        self._use_ann = use_ann and _HNSWLIB_AVAILABLE
        self._ann_threshold = ann_threshold
        self._ann_index: HNSWIndex | None = None
        self._init_tables()

        # Try to load existing ANN index
        if self._use_ann:
            self._load_ann_index()

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

    def _get_ann_index_path(self) -> Path:
        """Get the path for the ANN index file."""
        return self.db_path.parent / "ann_index.bin"

    def _load_ann_index(self) -> bool:
        """Try to load existing ANN index from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        index_path = self._get_ann_index_path()
        if index_path.exists():
            try:
                self._ann_index = HNSWIndex.load(index_path)
                logger.info(f"Loaded ANN index with {self._ann_index.count} items")
                return True
            except Exception as e:
                logger.warning(f"Failed to load ANN index: {e}")
        return False

    def _should_use_ann(self) -> bool:
        """Check if ANN should be used for search.

        Returns:
            True if ANN is enabled and has enough items
        """
        if not self._use_ann or self._ann_index is None:
            return False
        return self._ann_index.count >= self._ann_threshold

    def build_ann_index(self, force: bool = False) -> int:
        """Build or rebuild the ANN index from stored embeddings.

        Args:
            force: Force rebuild even if index exists

        Returns:
            Number of items indexed

        Raises:
            ImportError: If hnswlib is not available
        """
        if not _HNSWLIB_AVAILABLE:
            raise ImportError(
                "hnswlib is required for ANN search. "
                "Install with: uv sync --extra ann"
            )

        # Get all embeddings from database
        rows = self.conn.execute("""
            SELECT key, embedding FROM memory_embeddings
        """).fetchall()

        if not rows:
            logger.info("No embeddings to index")
            return 0

        # Create new index
        self._ann_index = HNSWIndex(
            dimension=self.dimension,
            max_elements=max(len(rows) * 2, 10000),
        )

        # Add all embeddings
        keys = [row[0] for row in rows]
        embeddings = [json.loads(row[1]) for row in rows]
        self._ann_index.add_items(keys, embeddings)

        # Save to disk
        self._ann_index.save(self._get_ann_index_path())

        logger.info(f"Built ANN index with {len(rows)} items")
        return len(rows)

    def save_ann_index(self) -> bool:
        """Save the ANN index to disk.

        Returns:
            True if saved, False if no index exists
        """
        if self._ann_index is None:
            return False

        self._ann_index.save(self._get_ann_index_path())
        return True

    @property
    def ann_enabled(self) -> bool:
        """Check if ANN is enabled and available."""
        return self._use_ann

    @property
    def ann_count(self) -> int:
        """Return the number of items in the ANN index."""
        if self._ann_index is None:
            return 0
        return self._ann_index.count

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

        # Add to ANN index if enabled
        if self._ann_index is not None:
            self._ann_index.add_item(key, embedding)

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

        # Add all to ANN index if enabled
        if self._ann_index is not None:
            keys = [item["key"] for item in items]
            self._ann_index.add_items(keys, embeddings)

        logger.info(f"Stored {len(items)} semantic memories in batch")
        return len(items)

    def search_semantic(
        self,
        query: str,
        namespace: str | None = None,
        top_k: int = 5,
        min_similarity: float = 0.0,
        use_ann: bool | None = None,
    ) -> list[SemanticSearchResult]:
        """Search memories by semantic similarity.

        Uses ANN (Approximate Nearest Neighbor) for fast search when enabled
        and the dataset is large enough. Falls back to brute force for small
        datasets or when namespace filtering is needed.

        Args:
            query: Search query text
            namespace: Optional namespace to search within (disables ANN)
            top_k: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0-1)
            use_ann: Force ANN on/off. None = auto-detect

        Returns:
            List of SemanticSearchResult sorted by similarity (highest first)
        """
        # Generate query embedding
        query_embedding = self._provider.embed(query)

        # Decide whether to use ANN
        # ANN doesn't support namespace filtering, so fall back to brute force
        should_use_ann = use_ann if use_ann is not None else self._should_use_ann()
        if namespace is not None:
            should_use_ann = False  # ANN doesn't support filtering

        if should_use_ann and self._ann_index is not None:
            return self._search_ann(query_embedding, top_k, min_similarity)

        return self._search_brute_force(query_embedding, namespace, top_k, min_similarity)

    def _search_ann(
        self,
        query_embedding: list[float],
        top_k: int,
        min_similarity: float,
    ) -> list[SemanticSearchResult]:
        """Search using ANN index.

        Args:
            query_embedding: Query vector
            top_k: Maximum results
            min_similarity: Minimum similarity threshold

        Returns:
            List of search results
        """
        # Get candidates from ANN
        candidates = self._ann_index.search(query_embedding, k=top_k * 2)

        # Filter by similarity and fetch full data
        results: list[SemanticSearchResult] = []

        for key, similarity in candidates:
            if similarity < min_similarity:
                continue

            # Fetch full memory data
            row = self.conn.execute(
                """
                SELECT m.value, m.namespace, m.metadata, m.created_at
                FROM memories m
                WHERE m.key = ?
                """,
                [key],
            ).fetchone()

            if row:
                value, ns, metadata_json, created_at = row
                metadata = json.loads(metadata_json) if metadata_json else {}
                results.append(SemanticSearchResult(
                    key=key,
                    value=value,
                    namespace=ns,
                    similarity=similarity,
                    metadata=metadata,
                    created_at=created_at,
                ))

            if len(results) >= top_k:
                break

        return results

    def _search_brute_force(
        self,
        query_embedding: list[float],
        namespace: str | None,
        top_k: int,
        min_similarity: float,
    ) -> list[SemanticSearchResult]:
        """Search using brute force cosine similarity.

        Args:
            query_embedding: Query vector
            namespace: Optional namespace filter
            top_k: Maximum results
            min_similarity: Minimum similarity threshold

        Returns:
            List of search results
        """
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
        # Delete from ANN index if enabled
        if self._ann_index is not None:
            self._ann_index.remove_item(key)

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

        Useful after changing the embedding model. Also rebuilds the ANN index
        if ANN is enabled.

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

        # Rebuild ANN index if enabled
        if self._use_ann:
            self.build_ann_index(force=True)

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

        stats = {
            "total_memories": memory_count,
            "memories_with_embeddings": embedding_count,
            "embedding_dimension": self.dimension,
            "embedding_model": "sentence-transformers",
            "by_namespace": {ns: count for ns, count in namespace_stats},
            "ann_enabled": self._use_ann,
            "ann_available": _HNSWLIB_AVAILABLE,
        }

        if self._ann_index is not None:
            stats["ann_index_count"] = self._ann_index.count
            stats["ann_threshold"] = self._ann_threshold
            stats["ann_active"] = self._should_use_ann()

        return stats

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

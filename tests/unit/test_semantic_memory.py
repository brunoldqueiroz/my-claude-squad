"""Tests for semantic memory with vector embeddings."""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Test whether semantic dependencies are available
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False


class TestSemanticMemoryAvailability:
    """Test availability checking."""

    def test_is_available_returns_bool(self):
        """is_available should return a boolean."""
        from orchestrator.semantic_memory import is_available
        result = is_available()
        assert isinstance(result, bool)

    def test_is_available_matches_imports(self):
        """is_available should match whether imports succeeded."""
        from orchestrator.semantic_memory import is_available
        assert is_available() == SEMANTIC_AVAILABLE


class TestSemanticSearchResult:
    """Test SemanticSearchResult dataclass."""

    def test_create_result(self):
        """Can create a SemanticSearchResult."""
        from orchestrator.semantic_memory import SemanticSearchResult

        result = SemanticSearchResult(
            key="test-key",
            value="test value",
            namespace="default",
            similarity=0.85,
            metadata={"tag": "test"},
            created_at=datetime.now(),
        )

        assert result.key == "test-key"
        assert result.value == "test value"
        assert result.namespace == "default"
        assert result.similarity == 0.85
        assert result.metadata == {"tag": "test"}
        assert isinstance(result.created_at, datetime)


class TestEmbeddingProvider:
    """Test EmbeddingProvider abstract base class."""

    def test_abstract_methods(self):
        """EmbeddingProvider should have abstract methods."""
        from orchestrator.semantic_memory import EmbeddingProvider

        # Cannot instantiate directly
        with pytest.raises(TypeError):
            EmbeddingProvider()


class TestCosineSimilarity:
    """Test cosine similarity function."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        from orchestrator.semantic_memory import cosine_similarity

        vec = [1.0, 2.0, 3.0]
        similarity = cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.001

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        from orchestrator.semantic_memory import cosine_similarity

        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.001

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        from orchestrator.semantic_memory import cosine_similarity

        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.001

    def test_zero_vector(self):
        """Zero vectors should return 0.0."""
        from orchestrator.semantic_memory import cosine_similarity

        vec1 = [0.0, 0.0]
        vec2 = [1.0, 1.0]
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == 0.0


@pytest.mark.skipif(not SEMANTIC_AVAILABLE, reason="sentence-transformers not installed")
class TestSentenceTransformerProvider:
    """Test SentenceTransformerProvider when dependencies are available."""

    def test_create_provider(self):
        """Can create a SentenceTransformerProvider."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider()
        assert provider._model_name == "all-MiniLM-L6-v2"

    def test_custom_model(self):
        """Can specify custom model name."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider(model_name="custom-model")
        assert provider._model_name == "custom-model"

    def test_lazy_loading(self):
        """Model should be lazily loaded."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider()
        assert provider._model is None

    def test_embed_single(self):
        """Can embed a single text."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider()
        embedding = provider.embed("Hello world")

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_batch(self):
        """Can embed multiple texts."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider()
        texts = ["Hello", "World", "Test"]
        embeddings = provider.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(isinstance(e, list) for e in embeddings)
        assert all(len(e) == len(embeddings[0]) for e in embeddings)

    def test_embed_batch_empty(self):
        """Empty batch returns empty list."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider()
        embeddings = provider.embed_batch([])
        assert embeddings == []

    def test_dimension_property(self):
        """Dimension property returns correct value."""
        from orchestrator.semantic_memory import SentenceTransformerProvider

        provider = SentenceTransformerProvider()
        dimension = provider.dimension
        assert dimension == 384  # all-MiniLM-L6-v2 is 384 dimensions


@pytest.mark.skipif(not SEMANTIC_AVAILABLE, reason="sentence-transformers not installed")
class TestSemanticMemory:
    """Test SemanticMemory class when dependencies are available."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a SemanticMemory instance with temp database."""
        from orchestrator.semantic_memory import SemanticMemory

        db_path = tmp_path / "test_memory.duckdb"
        return SemanticMemory(db_path=db_path)

    def test_create_memory(self, memory):
        """Can create SemanticMemory instance."""
        assert memory is not None
        assert memory.db_path.exists()

    def test_store_semantic(self, memory):
        """Can store a memory with embedding."""
        memory.store_semantic("key1", "The quick brown fox")

        # Verify embedding was stored
        assert memory.has_embedding("key1")

    def test_store_with_namespace(self, memory):
        """Can store in specific namespace."""
        memory.store_semantic("key1", "Test value", namespace="custom")

        # Should be searchable in that namespace
        results = memory.search_semantic("test", namespace="custom")
        assert len(results) == 1
        assert results[0].namespace == "custom"

    def test_store_with_metadata(self, memory):
        """Can store with metadata."""
        memory.store_semantic("key1", "Test", metadata={"tag": "important"})

        results = memory.search_semantic("test")
        assert results[0].metadata == {"tag": "important"}

    def test_search_semantic(self, memory):
        """Can search by semantic similarity."""
        memory.store_semantic("doc1", "Python is a programming language")
        memory.store_semantic("doc2", "JavaScript runs in browsers")
        memory.store_semantic("doc3", "Cats are furry animals")

        # Search for programming-related
        results = memory.search_semantic("coding languages", top_k=2)

        assert len(results) == 2
        # Programming languages should be more similar than cats
        assert results[0].key in ["doc1", "doc2"]

    def test_search_with_min_similarity(self, memory):
        """Can filter by minimum similarity."""
        memory.store_semantic("doc1", "Python programming language")
        memory.store_semantic("doc2", "Unrelated content about cooking")

        # With high threshold, may get fewer results
        results = memory.search_semantic(
            "Python coding", top_k=10, min_similarity=0.5
        )

        # At least the relevant doc should match
        assert any(r.key == "doc1" for r in results)

    def test_search_by_namespace(self, memory):
        """Can search within specific namespace."""
        memory.store_semantic("doc1", "Python programming", namespace="tech")
        memory.store_semantic("doc2", "JavaScript coding", namespace="tech")
        memory.store_semantic("doc3", "Cooking recipes", namespace="food")

        results = memory.search_semantic("programming", namespace="tech")
        assert all(r.namespace == "tech" for r in results)

    def test_get_embedding(self, memory):
        """Can retrieve embedding for a key."""
        memory.store_semantic("key1", "Test value")

        embedding = memory.get_embedding("key1")
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension

    def test_get_embedding_not_found(self, memory):
        """Returns None for non-existent key."""
        embedding = memory.get_embedding("nonexistent")
        assert embedding is None

    def test_has_embedding(self, memory):
        """Can check if embedding exists."""
        memory.store_semantic("key1", "Test")

        assert memory.has_embedding("key1")
        assert not memory.has_embedding("nonexistent")

    def test_delete_embedding(self, memory):
        """Can delete an embedding."""
        memory.store_semantic("key1", "Test")
        assert memory.has_embedding("key1")

        result = memory.delete_embedding("key1")
        assert result is True
        assert not memory.has_embedding("key1")

    def test_delete_embedding_not_found(self, memory):
        """Returns False when deleting non-existent embedding."""
        result = memory.delete_embedding("nonexistent")
        assert result is False

    def test_delete_semantic(self, memory):
        """Can delete both memory and embedding."""
        memory.store_semantic("key1", "Test")

        result = memory.delete_semantic("key1")
        assert result is True
        assert not memory.has_embedding("key1")

    def test_store_semantic_batch(self, memory):
        """Can store multiple items efficiently."""
        items = [
            {"key": "doc1", "value": "First document"},
            {"key": "doc2", "value": "Second document"},
            {"key": "doc3", "value": "Third document", "metadata": {"order": 3}},
        ]

        count = memory.store_semantic_batch(items)
        assert count == 3

        assert memory.has_embedding("doc1")
        assert memory.has_embedding("doc2")
        assert memory.has_embedding("doc3")

    def test_store_semantic_batch_empty(self, memory):
        """Empty batch returns 0."""
        count = memory.store_semantic_batch([])
        assert count == 0

    def test_reindex_all(self, memory):
        """Can reindex all memories."""
        memory.store_semantic("doc1", "First document")
        memory.store_semantic("doc2", "Second document")

        count = memory.reindex_all()
        assert count == 2

    def test_get_stats(self, memory):
        """Can get statistics."""
        memory.store_semantic("doc1", "First", namespace="ns1")
        memory.store_semantic("doc2", "Second", namespace="ns2")

        stats = memory.get_stats()

        assert stats["total_memories"] >= 2
        assert stats["memories_with_embeddings"] >= 2
        assert stats["embedding_dimension"] == 384
        assert "by_namespace" in stats

    def test_close(self, memory):
        """Can close the database connection."""
        memory.close()
        # Connection should be closed, further operations may fail

    def test_dimension_property(self, memory):
        """Dimension property returns embedding size."""
        assert memory.dimension == 384


@pytest.mark.skipif(not SEMANTIC_AVAILABLE, reason="sentence-transformers not installed")
class TestSemanticMemorySingleton:
    """Test singleton pattern for SemanticMemory."""

    def test_get_semantic_memory_returns_instance(self):
        """get_semantic_memory returns SemanticMemory instance."""
        from orchestrator.semantic_memory import get_semantic_memory, SemanticMemory

        memory = get_semantic_memory()
        assert isinstance(memory, SemanticMemory)

    def test_get_semantic_memory_is_singleton(self):
        """get_semantic_memory returns same instance."""
        from orchestrator.semantic_memory import get_semantic_memory

        memory1 = get_semantic_memory()
        memory2 = get_semantic_memory()
        assert memory1 is memory2


class TestSemanticMemoryUnavailable:
    """Test behavior when semantic dependencies are not available."""

    def test_import_error_message(self):
        """SentenceTransformerProvider raises ImportError with instructions."""
        if SEMANTIC_AVAILABLE:
            pytest.skip("Dependencies are available")

        from orchestrator.semantic_memory import SentenceTransformerProvider

        with pytest.raises(ImportError) as exc_info:
            SentenceTransformerProvider()

        assert "uv sync --extra semantic" in str(exc_info.value)

    def test_semantic_memory_import_error(self):
        """SemanticMemory raises ImportError with instructions."""
        if SEMANTIC_AVAILABLE:
            pytest.skip("Dependencies are available")

        from orchestrator.semantic_memory import SemanticMemory

        with pytest.raises(ImportError) as exc_info:
            SemanticMemory()

        assert "uv sync --extra semantic" in str(exc_info.value)

    def test_get_semantic_memory_returns_none(self):
        """get_semantic_memory returns None when unavailable."""
        if SEMANTIC_AVAILABLE:
            pytest.skip("Dependencies are available")

        from orchestrator.semantic_memory import get_semantic_memory

        memory = get_semantic_memory()
        assert memory is None


class TestMCPToolsWithoutSemantic:
    """Test MCP tools graceful degradation when semantic is unavailable."""

    def test_semantic_store_returns_error(self):
        """semantic_store returns error when unavailable."""
        from orchestrator.semantic_memory import is_available

        if not is_available():
            # When sentence-transformers is not installed, the tools should
            # check is_available() and return an error dict.
            # We test the pattern by checking the function behavior directly.

            # Import the function definition (not the decorated tool)
            # Since we can't easily call the FastMCP tool, we test the core logic
            from orchestrator import server

            # The tool fn attribute contains the underlying function
            result = server.semantic_store.fn("key", "value")
            assert result["success"] is False
            assert "not available" in result["error"]

    def test_semantic_search_returns_error(self):
        """semantic_search returns error when unavailable."""
        from orchestrator.semantic_memory import is_available
        if not is_available():
            from orchestrator import server
            result = server.semantic_search.fn("query")
            assert result["success"] is False
            assert "not available" in result["error"]

    def test_semantic_stats_returns_unavailable(self):
        """semantic_stats indicates unavailable status."""
        from orchestrator.semantic_memory import is_available
        if not is_available():
            from orchestrator import server
            result = server.semantic_stats.fn()
            assert result["success"] is False
            assert result["available"] is False


@pytest.mark.skipif(not SEMANTIC_AVAILABLE, reason="sentence-transformers not installed")
class TestMCPToolsWithSemantic:
    """Test MCP tools when semantic memory is available."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a semantic memory for testing."""
        from orchestrator.semantic_memory import SemanticMemory

        return SemanticMemory(db_path=tmp_path / "test.duckdb")

    def test_semantic_store_success(self, memory):
        """semantic_store stores memory with embedding."""
        from orchestrator import server

        with patch.object(server, "get_semantic_memory", return_value=memory):
            result = server.semantic_store.fn("key1", "Test value", namespace="test")

        assert result["success"] is True
        assert result["key"] == "key1"
        assert result["has_embedding"] is True
        assert result["embedding_dimension"] == 384

    def test_semantic_search_success(self, memory):
        """semantic_search finds similar memories."""
        from orchestrator import server

        with patch.object(server, "get_semantic_memory", return_value=memory):
            # Store some data
            server.semantic_store.fn("doc1", "Python programming language")
            server.semantic_store.fn("doc2", "JavaScript web development")

            # Search
            result = server.semantic_search.fn("coding", top_k=2)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["results"]) == 2

    def test_semantic_store_batch_success(self, memory):
        """semantic_store_batch stores multiple items."""
        from orchestrator import server

        items = [
            {"key": "k1", "value": "Value 1"},
            {"key": "k2", "value": "Value 2"},
        ]

        with patch.object(server, "get_semantic_memory", return_value=memory):
            result = server.semantic_store_batch.fn(items, namespace="batch")

        assert result["success"] is True
        assert result["stored_count"] == 2

    def test_semantic_store_batch_validation(self, memory):
        """semantic_store_batch validates items."""
        from orchestrator import server

        # Missing 'value' field
        items = [{"key": "k1"}]

        with patch.object(server, "get_semantic_memory", return_value=memory):
            result = server.semantic_store_batch.fn(items)

        assert result["success"] is False
        assert "missing" in result["error"].lower()

    def test_semantic_stats_success(self, memory):
        """semantic_stats returns statistics."""
        from orchestrator import server

        with patch.object(server, "get_semantic_memory", return_value=memory):
            server.semantic_store.fn("doc1", "Test")
            result = server.semantic_stats.fn()

        assert result["success"] is True
        assert result["available"] is True
        assert "total_memories" in result

    def test_semantic_reindex_success(self, memory):
        """semantic_reindex regenerates embeddings."""
        from orchestrator import server

        with patch.object(server, "get_semantic_memory", return_value=memory):
            server.semantic_store.fn("doc1", "Test")
            server.semantic_store.fn("doc2", "Another test")
            result = server.semantic_reindex.fn()

        assert result["success"] is True
        assert result["reindexed_count"] == 2

    def test_semantic_delete_success(self, memory):
        """semantic_delete removes memory and embedding."""
        from orchestrator import server

        with patch.object(server, "get_semantic_memory", return_value=memory):
            server.semantic_store.fn("doc1", "Test")
            result = server.semantic_delete.fn("doc1")

        assert result["success"] is True
        assert result["key"] == "doc1"

    def test_semantic_delete_not_found(self, memory):
        """semantic_delete handles not found."""
        from orchestrator import server

        with patch.object(server, "get_semantic_memory", return_value=memory):
            result = server.semantic_delete.fn("nonexistent")

        assert result["success"] is False
        assert "not found" in result["message"]

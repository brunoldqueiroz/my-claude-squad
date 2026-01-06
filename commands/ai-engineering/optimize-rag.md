---
name: optimize-rag
description: Analyze and optimize an existing RAG pipeline
agent: rag-specialist
arguments:
  - name: path
    description: Path to the RAG application or specific file
    required: false
    default: "."
  - name: focus
    description: "Optimization focus (retrieval, generation, latency, cost, all)"
    required: false
    default: all
---

# Optimize RAG Pipeline

Analyze an existing RAG system and provide optimization recommendations.

## Usage

```
/optimize-rag
/optimize-rag ./src/rag --focus retrieval
/optimize-rag ./my-rag-app --focus cost
```

## Analysis Areas

### Retrieval Optimization
- Chunk size and overlap analysis
- Embedding model evaluation
- Hybrid search implementation
- Reranking integration
- Metadata filtering usage

### Generation Optimization
- Prompt template analysis
- Context window usage
- Response quality checks
- Citation extraction

### Latency Optimization
- Embedding caching
- Query batching
- Async processing
- Connection pooling

### Cost Optimization
- Model tiering recommendations
- Caching strategies
- Token usage analysis
- Batch processing opportunities

## Agent Assignment

This command uses the **rag-specialist** agent.

## What Gets Analyzed

```
Files Examined:
├── Chunking configuration
├── Embedding model setup
├── Vector store configuration
├── Retrieval logic
├── Prompt templates
└── LLM integration
```

## Output Format

```markdown
# RAG Optimization Report

## Current Configuration
- Chunk size: 512 tokens
- Overlap: 50 tokens
- Embedding: text-embedding-3-small
- Vector DB: Qdrant
- Retrieval: Top-5 semantic search

## Issues Found

### 🔴 Critical
1. No chunk overlap causing context loss at boundaries

### 🟡 Warning
1. Using only semantic search (missing keyword matches)
2. No reranking step

### 🟢 Good
1. Appropriate chunk size for content type

## Recommendations

### Retrieval Improvements
1. **Add hybrid search**
   - Combine semantic (70%) + BM25 (30%)
   - Expected: +15% recall improvement

2. **Implement reranking**
   - Add Cohere rerank-english-v3.0
   - Expected: +10% precision improvement

### Cost Optimizations
1. **Cache embeddings**
   - Current: ~$X/month
   - With cache: ~$Y/month (Z% reduction)

## Implementation Snippets

### Add Hybrid Search
```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

ensemble = EnsembleRetriever(
    retrievers=[bm25, vector],
    weights=[0.3, 0.7]
)
```

## Evaluation Metrics

Run these to measure improvements:
```python
from ragas import evaluate
from ragas.metrics import faithfulness, context_precision

results = evaluate(dataset, metrics=[faithfulness, context_precision])
```
```

## Common Optimizations

| Issue | Solution | Impact |
|-------|----------|--------|
| Low recall | Add hybrid search | +10-20% recall |
| Irrelevant results | Add reranking | +10-15% precision |
| Slow queries | Cache embeddings | -50% latency |
| High costs | Model tiering | -30-50% cost |
| Context loss | Increase overlap | Better coherence |
| Missed keywords | Add BM25 | Better exact match |

## Evaluation Tools

The agent will recommend evaluation using:
- **RAGAS**: Faithfulness, relevance, precision, recall
- **DeepEval**: Hallucination detection, answer relevancy
- **Custom metrics**: Domain-specific evaluations

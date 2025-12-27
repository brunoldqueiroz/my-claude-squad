# AI Engineering Patterns

Reference patterns for building AI applications including RAG, multi-agent systems, LLM integration, and automation.

---

## RAG Architecture Patterns

### 1. Naive RAG
Basic retrieve-then-generate pattern.

```
Query → Embed → Vector Search → Top-K Chunks → LLM → Response
```

**Use when**: Simple Q&A, small document sets, low latency requirements.

### 2. Advanced RAG
Enhanced retrieval with preprocessing and postprocessing.

```
Query → Query Rewriting → Hybrid Search → Reranking → Context Compression → LLM → Response
```

**Enhancements**:
- Query expansion/rewriting
- Hybrid search (semantic + keyword)
- Cross-encoder reranking
- Context compression
- Citation extraction

### 3. Agentic RAG
Agent-driven retrieval with tool use and iteration.

```
Query → Agent → [Tool: Search] → [Tool: Summarize] → [Tool: Verify] → Response
```

**Use when**: Complex queries, multi-hop reasoning, verification required.

---

## Vector Database Selection

| Database | Best For | Deployment | Cost |
|----------|----------|------------|------|
| **ChromaDB** | Prototyping, local dev | Embedded/Docker | Free |
| **Qdrant** | Production, filtering | Self-hosted/Cloud | Free/Paid |
| **Weaviate** | Hybrid search, schemas | Self-hosted/Cloud | Free/Paid |
| **Pinecone** | Managed, scale | Cloud only | Paid |
| **pgvector** | Existing Postgres | Self-hosted | Free |
| **Milvus** | Large scale, GPU | Self-hosted/Cloud | Free/Paid |

### Selection Criteria
- **Prototyping**: ChromaDB (simple, embedded)
- **Production + Postgres**: pgvector (no new infra)
- **Production + Scale**: Qdrant or Pinecone
- **Hybrid Search**: Weaviate (native BM25 + vector)

---

## Chunking Strategies

### Fixed-Size Chunking
```python
chunk_size = 512
chunk_overlap = 50
```
**Use when**: Uniform content, simple implementation.

### Semantic Chunking
Split by meaning boundaries (paragraphs, sections).
**Use when**: Structured documents, preserving context.

### Recursive Chunking
Hierarchical splitting with fallbacks.
```python
separators = ["\n\n", "\n", ". ", " "]
```
**Use when**: Mixed content types, varying structure.

### Document-Aware Chunking
Respect document structure (headers, tables, code blocks).
**Use when**: Technical docs, markdown, code.

---

## Embedding Model Selection

| Model | Dimensions | Quality | Speed | Cost |
|-------|------------|---------|-------|------|
| `text-embedding-3-small` | 1536 | Good | Fast | Low |
| `text-embedding-3-large` | 3072 | Best | Medium | Medium |
| `nomic-embed-text` | 768 | Good | Fast | Free (local) |
| `bge-large-en-v1.5` | 1024 | Good | Medium | Free (local) |
| `voyage-3` | 1024 | Best | Medium | Paid |

---

## Multi-Agent Design Patterns

### 1. Sequential Pipeline
Agents execute in order, passing results.
```
Agent A → Agent B → Agent C → Final Output
```
**Use when**: Linear workflows, clear dependencies.

### 2. Parallel Fan-Out
Multiple agents work simultaneously.
```
        → Agent A →
Input  → Agent B → Aggregator → Output
        → Agent C →
```
**Use when**: Independent subtasks, speed optimization.

### 3. Hierarchical Orchestration
Supervisor delegates to specialists.
```
Supervisor → [Researcher, Writer, Reviewer] → Supervisor → Output
```
**Use when**: Complex tasks, role-based collaboration.

### 4. Collaborative Debate
Agents discuss and refine.
```
Agent A ↔ Agent B → Consensus → Output
```
**Use when**: Quality-critical outputs, diverse perspectives.

---

## Framework Comparison

| Framework | Architecture | State Mgmt | Best For |
|-----------|--------------|------------|----------|
| **LangGraph** | Graph-based | Built-in | Complex workflows, cycles |
| **CrewAI** | Role-based | Automatic | Team collaboration |
| **AutoGen** | Conversational | Session | Research, debate |
| **OpenAI Swarm** | Handoff | Minimal | Simple routing |

### LangGraph Key Patterns
```python
# Nodes represent functions
# Edges define flow
# State persists across nodes
graph.add_node("research", research_fn)
graph.add_edge("research", "write")
graph.add_conditional_edges("review", decide_next)
```

### CrewAI Key Patterns
```python
# Agents have roles and goals
# Tasks have descriptions and expected outputs
# Crews orchestrate agents
researcher = Agent(role="Researcher", goal="Find facts")
writer = Agent(role="Writer", goal="Write content")
crew = Crew(agents=[researcher, writer], tasks=[...])
```

---

## LLM Integration Patterns

### Structured Outputs
```python
from pydantic import BaseModel

class Response(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

response = client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_schema", "json_schema": Response.model_json_schema()}
)
```

### Streaming
```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

### Retry with Backoff
```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(3))
def call_llm(prompt):
    return client.chat.completions.create(...)
```

---

## MCP Server Development

### Basic Structure
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({
  name: "my-mcp-server",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {},
    resources: {}
  }
});

// Register tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "my_tool",
    description: "Does something useful",
    inputSchema: { type: "object", properties: {...} }
  }]
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "my_tool") {
    // Implementation
    return { content: [{ type: "text", text: result }] };
  }
});
```

### Python MCP Server
```python
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("my-server")

@app.list_tools()
async def list_tools():
    return [Tool(name="my_tool", description="...", inputSchema={...})]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_tool":
        result = do_something(arguments)
        return [TextContent(type="text", text=result)]
```

---

## Cost Optimization Strategies

### 1. Model Tiering
- Use cheaper models for simple tasks
- Reserve expensive models for complex reasoning

### 2. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str) -> list[float]:
    return embed_model.encode(text)
```

### 3. Token Optimization
- Compress context before sending
- Use summaries instead of full documents
- Implement sliding window for long conversations

### 4. Batch Processing
```python
# Batch embeddings instead of one-by-one
embeddings = embed_model.encode(texts, batch_size=32)
```

---

## RAG Evaluation Metrics

| Metric | Measures | Tool |
|--------|----------|------|
| **Faithfulness** | Answer grounded in context | RAGAS, DeepEval |
| **Answer Relevance** | Answer addresses query | RAGAS |
| **Context Precision** | Retrieved chunks useful | RAGAS |
| **Context Recall** | All needed info retrieved | RAGAS |
| **Hallucination** | Unsupported claims | DeepEval |

### Basic Evaluation
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy]
)
```

---

## LLM Observability

### Observability Platforms
| Platform | Type | Best For |
|----------|------|----------|
| **Langfuse** | Open source | Full tracing, prompt management, evals |
| **LangSmith** | LangChain native | LangChain/LangGraph apps |
| **Arize Phoenix** | Open source | ML + LLM observability |
| **Weights & Biases** | ML platform | Experiment tracking |

### Key Metrics to Track
- **Latency**: Time to first token, total response time
- **Token Usage**: Input/output tokens per request
- **Cost**: Per-request and aggregate costs
- **Quality Scores**: Faithfulness, relevance, hallucination
- **Error Rates**: API failures, parsing errors

### Langfuse Tracing Pattern
```python
from langfuse import observe

@observe()
def rag_pipeline(query: str):
    """Auto-traced function"""
    docs = retrieve(query)
    response = generate(query, docs)
    return response

@observe(as_type="generation")
def generate(query: str, context: list):
    """Generation span with model details"""
    # LLM call here
    pass
```

### LangChain Callback Integration
```python
from langfuse.langchain import CallbackHandler

handler = CallbackHandler()
handler.set_trace_params(
    name="RAG Pipeline",
    user_id="user-123"
)

chain.invoke(input, config={"callbacks": [handler]})
```

---

## Common Anti-Patterns

### RAG Anti-Patterns
- Chunking without overlap (loses context)
- Using only semantic search (misses keywords)
- Not reranking results (irrelevant context)
- Stuffing too much context (dilutes relevance)

### Agent Anti-Patterns
- No clear stopping conditions (infinite loops)
- Agents without specific goals (unfocused)
- No human-in-the-loop for critical decisions
- Sharing state incorrectly between agents

### LLM Anti-Patterns
- Hardcoding prompts without version control
- Not handling rate limits
- Ignoring token limits until failure
- Not validating structured outputs
- No observability (flying blind in production)

---

## Research Tools

When implementing AI patterns, verify with:

| Tool | Use For |
|------|---------|
| `mcp__upstash-context7-mcp__get-library-docs` | LangChain, LlamaIndex, CrewAI docs |
| `mcp__exa__get_code_context_exa` | Code examples, implementation patterns |
| `WebSearch` | Latest best practices, new releases |

### Libraries to Always Verify
- `langchain` / `langgraph` - Frequent breaking changes
- `llama-index` - API evolves rapidly
- `crewai` - New features added often
- `openai` - Model updates, new parameters
- `langfuse` - SDK updates, new integrations

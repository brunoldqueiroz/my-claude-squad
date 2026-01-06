---
name: create-chatbot
description: Generate chatbot application boilerplate
agent: automation-specialist
arguments:
  - name: name
    description: Name of the chatbot
    required: true
  - name: type
    description: "Chatbot type (simple, rag, agent)"
    required: false
    default: rag
  - name: platform
    description: "Deployment platform (fastapi, dify, n8n)"
    required: false
    default: fastapi
---

# Create Chatbot

Generate a chatbot application with your choice of architecture and platform.

## Usage

```
/create-chatbot support-bot
/create-chatbot sales-assistant --type agent --platform fastapi
/create-chatbot help-desk --type rag --platform dify
```

## What Gets Created

### FastAPI (default)
```
{name}/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── main.py             # FastAPI app
│   ├── chat.py             # Chat logic
│   ├── memory.py           # Conversation memory
│   └── rag.py              # RAG integration (if type=rag)
├── static/
│   └── index.html          # Simple chat UI
├── tests/
│   └── test_chat.py        # Chat tests
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

### Dify
```
{name}/
├── dify_app.yaml           # Dify application config
├── prompts/
│   ├── system.txt          # System prompt
│   └── examples.txt        # Few-shot examples
├── knowledge/
│   └── .gitkeep            # Knowledge base documents
└── README.md
```

### n8n
```
{name}/
├── workflow.json           # n8n workflow export
├── prompts/
│   └── system.txt          # System prompt
└── README.md
```

## Chatbot Types

| Type | Features |
|------|----------|
| `simple` | Basic LLM chat, conversation memory |
| `rag` | Knowledge base retrieval, citations |
| `agent` | Tool use, multi-step reasoning |

## Agent Assignment

This command uses the **automation-specialist** agent.

## Example Generated Code

### FastAPI Chat Endpoint
```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI()

class ChatMessage(BaseModel):
    message: str
    session_id: str

@app.post("/chat")
async def chat(request: ChatMessage):
    history = get_history(request.session_id)

    response = await generate_response(
        message=request.message,
        history=history
    )

    save_to_history(request.session_id, request.message, response)
    return {"response": response}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid4())

    while True:
        message = await websocket.receive_text()
        response = await generate_response(message, get_history(session_id))
        await websocket.send_text(response)
```

### Dify Configuration
```yaml
app_type: chatbot
model:
  provider: openai
  name: gpt-4o
  temperature: 0.7

system_prompt: |
  You are a helpful customer support assistant.
  Be friendly, professional, and concise.

knowledge_base:
  enabled: true
  retrieval_model: semantic
  top_k: 5

features:
  citation: true
  suggested_questions: true
```

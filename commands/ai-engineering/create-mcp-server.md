---
name: create-mcp-server
description: Generate MCP (Model Context Protocol) server template
arguments:
  - name: name
    description: Name of the MCP server
    required: true
  - name: language
    description: "Implementation language (typescript, python)"
    required: false
    default: typescript
  - name: tools
    description: "Comma-separated list of tool names to create"
    required: false
---

# Create MCP Server

Generate an MCP server that exposes custom tools and resources for Claude.

## Usage

```
/create-mcp-server database-tools
/create-mcp-server api-server --language python --tools search,create,update
/create-mcp-server file-manager --tools read_file,write_file,list_dir
```

## What Gets Created

### TypeScript (default)
```
{name}/
├── src/
│   ├── index.ts            # Server entry point
│   ├── tools/
│   │   ├── index.ts        # Tool registry
│   │   └── {tool}.ts       # Individual tools
│   ├── resources/
│   │   └── index.ts        # Resource handlers
│   └── types.ts            # Type definitions
├── tests/
│   └── tools.test.ts       # Tool tests
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

### Python
```
{name}/
├── src/
│   ├── __init__.py
│   ├── server.py           # Server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   └── {tool}.py       # Individual tools
│   └── resources/
│       └── __init__.py     # Resource handlers
├── tests/
│   └── test_tools.py       # Tool tests
├── pyproject.toml
├── .env.example
└── README.md
```

## MCP Capabilities

| Capability | Description |
|------------|-------------|
| **Tools** | Functions Claude can call |
| **Resources** | Files/data Claude can read |
| **Prompts** | Reusable prompt templates |

## Agent Assignment

This command uses the **automation-specialist** agent.

## Example Generated Code

### TypeScript Server
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "{name}", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "search",
      description: "Search for items",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" }
        },
        required: ["query"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "search":
      const results = await performSearch(args.query);
      return { content: [{ type: "text", text: JSON.stringify(results) }] };
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python Server
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("{name}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search",
            description="Search for items",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search":
        results = await perform_search(arguments["query"])
        return [TextContent(type="text", text=str(results))]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Claude Desktop Config
```json
{
  "mcpServers": {
    "{name}": {
      "command": "node",
      "args": ["path/to/{name}/build/index.js"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

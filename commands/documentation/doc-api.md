---
description: Generate API documentation from code
argument-hint: [api path or file]
---

# Document API

Generate API documentation from FastAPI, Flask, or other Python API code.

## Usage

```
/doc-api [api path or file]
```

## Supported Frameworks

- **FastAPI**: Extracts from Pydantic models and route decorators
- **Flask**: Extracts from route decorators and docstrings
- **Django REST**: Extracts from ViewSets and serializers

## Analysis

1. **Discover Endpoints**:
   - HTTP methods (GET, POST, PUT, DELETE)
   - URL paths and parameters
   - Request/response schemas

2. **Extract Schemas**:
   - Pydantic models
   - Request body structures
   - Response formats

3. **Generate Documentation**:
   - OpenAPI/Swagger spec
   - Markdown documentation
   - Example requests

## Generated Files

```
docs/
├── api/
│   ├── README.md         # API overview
│   ├── endpoints.md      # Endpoint reference
│   ├── schemas.md        # Data schemas
│   └── examples.md       # Request examples
└── openapi.json          # OpenAPI specification
```

## Endpoint Documentation

```markdown
## POST /api/orders

Create a new order.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| customer_id | integer | Yes | Customer identifier |
| items | array | Yes | Order line items |
| notes | string | No | Order notes |

### Example Request

```bash
curl -X POST https://api.example.com/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "customer_id": 12345,
    "items": [
      {"product_id": "prod-1", "quantity": 2}
    ]
  }'
```

### Response

**200 OK**
```json
{
  "order_id": "ord-123",
  "status": "pending",
  "created_at": "2024-01-15T14:30:00Z"
}
```

### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Invalid request body |
| 401 | Unauthorized |
| 404 | Customer not found |
```

## Features

- Auto-detect endpoint documentation
- Generate curl examples
- Include authentication details
- Document error responses
- Create OpenAPI 3.0 spec

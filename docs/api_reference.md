# Reflexia API Reference

This document provides a comprehensive reference for the Reflexia Model Manager API, enabling programmatic access to all functionality.

## API Endpoints

All API endpoints are available at the base URL of your Reflexia instance (e.g., `http://localhost:8000`).

### Health Check

```http
GET /healthz
```

Checks the health of the application and its services.

**Response** (200 OK):
```json
{
  "status": "ok",
  "timestamp": 1617123456.789,
  "version": "1.0.0",
  "services": {
    "model": true,
    "memory": true,
    "rag": true
  }
}
```

### Document Management

#### List Documents

```http
GET /api/documents
```

Returns a list of all documents in the RAG knowledge base.

**Authentication**: Required when `ENABLE_AUTH=true`  
**Rate Limit**: 60 requests per minute

**Response** (200 OK):
```json
{
  "documents": [
    {
      "id": "doc123",
      "filename": "article.pdf",
      "metadata": {
        "mime_type": "application/pdf",
        "page_count": 5,
        "created_at": "2025-04-02T12:30:45Z"
      }
    }
  ]
}
```

#### Delete Document

```http
DELETE /api/documents/{doc_id}
```

Removes a document from the RAG knowledge base.

**Parameters**:
- `doc_id` (path parameter): The unique identifier of the document to delete

**Authentication**: Required when `ENABLE_AUTH=true`  
**Rate Limit**: 60 requests per minute

**Response** (200 OK):
```json
{
  "success": true
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Document not found"
}
```

#### Upload Document

```http
POST /api/upload
```

Uploads a document to the RAG knowledge base.

**Content-Type**: `multipart/form-data`

**Form Parameters**:
- `file`: The document file to upload

**Authentication**: Required when `ENABLE_AUTH=true`  
**Rate Limit**: 10 requests per minute

**Response** (200 OK):
```json
{
  "success": true,
  "filename": "document.pdf"
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid file type. Allowed types: .txt, .md, .pdf, .csv, .json, .docx, .xlsx"
}
```

### Text Generation

#### Generate Response

```http
POST /api/generate
```

Generates a text response based on the provided prompt.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "system_prompt": "You are a helpful AI assistant.",
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 500,
  "use_rag": false
}
```

**Parameters**:
- `prompt` (required): The user prompt
- `system_prompt` (optional): System prompt for AI behavior
- `temperature` (optional): Sampling temperature (0.0-1.0, default: 0.7)
- `top_p` (optional): Nucleus sampling parameter (0.0-1.0, default: 0.9)
- `max_tokens` (optional): Maximum tokens to generate (default: 500)
- `use_rag` (optional): Whether to use RAG for enhanced responses (default: false)

**Authentication**: Required when `ENABLE_AUTH=true`  
**Rate Limit**: 30 requests per minute

**Response** (200 OK):
```json
{
  "response": "Quantum computing uses the principles of quantum physics to process information...",
  "processing_time": 1.25,
  "sources": []
}
```

When `use_rag` is true and sources are found, the response includes source references:

```json
{
  "response": "Quantum computing uses the principles of quantum physics to process information...",
  "processing_time": 2.7,
  "sources": [
    {
      "id": "doc123",
      "filename": "quantum_primer.pdf",
      "relevance": 0.92
    }
  ]
}
```

### Metrics

```http
GET /metrics
```

Returns Prometheus metrics in the standard text format.

**Response** (200 OK):
```
# HELP reflexia_memory_usage_bytes Current memory usage in bytes
# TYPE reflexia_memory_usage_bytes gauge
reflexia_memory_usage_bytes 1073741824
# HELP reflexia_memory_usage_percent Current memory usage as percentage
# TYPE reflexia_memory_usage_percent gauge
reflexia_memory_usage_percent 25.3
```

## Client Libraries

### Python Client

```python
from reflexia_client import ReflexiaClient

client = ReflexiaClient(base_url="http://localhost:8000", api_key="your-api-key")

# Generate a response
response = client.generate(
    prompt="Explain quantum computing",
    temperature=0.7,
    use_rag=True
)
print(response.text)

# List documents
documents = client.list_documents()
for doc in documents:
    print(f"Document: {doc.filename}")

# Upload a document
result = client.upload_document("path/to/document.pdf")
print(f"Upload success: {result.success}")
```

### JavaScript/TypeScript Client

```typescript
import { ReflexiaClient } from 'reflexia-client';

const client = new ReflexiaClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key' 
});

// Generate a response
client.generate({
  prompt: 'Explain quantum computing',
  temperature: 0.7,
  useRag: true
})
.then(response => {
  console.log(response.text);
})
.catch(error => {
  console.error('Error:', error);
});

// List documents
client.listDocuments()
  .then(documents => {
    documents.forEach(doc => {
      console.log(`Document: ${doc.filename}`);
    });
  });

// Upload a document
client.uploadDocument('path/to/document.pdf')
  .then(result => {
    console.log(`Upload success: ${result.success}`);
  });
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": "Error message description",
  "status": 400,
  "success": false
}
```

Common HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | OK - Request succeeded |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - Resource not found |
| 415 | Unsupported Media Type - Invalid content type |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |

## Versioning

The current API version is v1. The version is included in the health check response.

Future API changes will use semantic versioning principles:
- Backward compatible changes will increase the minor version
- Breaking changes will increase the major version

## Rate Limiting

See the [API Authentication Guide](api_auth.md) for details on rate limiting.
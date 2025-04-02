# Reflexia API Authentication Guide

This guide explains how to secure and authenticate with the Reflexia Model Manager API endpoints.

## Authentication Methods

Reflexia supports API key authentication for all REST API endpoints. Authentication can be enabled or disabled through configuration.

### Enabling Authentication

To enable API authentication:

1. Set the `ENABLE_AUTH` environment variable to `true` in your `.env` file or environment:
   ```
   ENABLE_AUTH=true
   ```

2. Set a secure API key:
   ```
   API_KEY=your-secure-random-key-here
   ```

> **Security Note**: Use a strong, randomly generated API key. We recommend at least 32 characters of random alphanumeric content.

### Using API Keys in Requests

When authentication is enabled, you must include the API key in each request to protected endpoints using the `X-API-Key` header:

```http
GET /api/documents HTTP/1.1
Host: localhost:8000
X-API-Key: your-secure-random-key-here
```

Example with curl:

```bash
curl -X GET "http://localhost:8000/api/documents" \
  -H "X-API-Key: your-secure-random-key-here"
```

Example with Python requests:

```python
import requests

headers = {
    "X-API-Key": "your-secure-random-key-here"
}

response = requests.get("http://localhost:8000/api/documents", headers=headers)
print(response.json())
```

## Rate Limiting

All API endpoints are protected by rate limiting, regardless of whether authentication is enabled. Rate limits apply to:

- API key (when authentication is enabled)
- IP address (always applied)

Default rate limits:

| Endpoint | Limit | Period | Notes |
|----------|-------|--------|-------|
| General API | 60 | 60 seconds | 1 request per second on average |
| File uploads | 10 | 60 seconds | More restrictive due to resource intensity |

Rate limit configuration can be adjusted in your environment variables:

```
API_RATE_LIMIT=60
API_RATE_PERIOD=60
UPLOAD_RATE_LIMIT=10
UPLOAD_RATE_PERIOD=60
```

## Protected Endpoints

The following endpoints require authentication when `ENABLE_AUTH` is set to `true`:

- `GET /api/documents` - List documents
- `DELETE /api/documents/{doc_id}` - Delete a document
- `POST /api/upload` - Upload a document
- `POST /api/generate` - Generate a response

## Authentication Flow

1. Client includes the API key in the request header
2. Server validates the API key using constant-time comparison to prevent timing attacks
3. If valid, the server checks rate limits for the API key
4. If rate limits are not exceeded, the request is processed
5. If invalid or rate limited, an appropriate error response is returned

## Error Responses

Authentication and rate limiting errors return standard HTTP status codes:

- `401 Unauthorized` - Invalid or missing API key
- `429 Too Many Requests` - Rate limit exceeded

Example error response:

```json
{
  "error": "Unauthorized: Invalid API key",
  "status": 401,
  "success": false
}
```

## Best Practices

1. **Do not hardcode API keys** in client-side code or public repositories
2. Rotate API keys periodically for enhanced security
3. Use environment variables or secure vaults to store API keys
4. Implement client-side retry logic with exponential backoff for rate limiting
5. Consider using separate API keys for different clients or services

## Implementation Details

The authentication mechanism uses constant-time comparison to prevent timing attacks. This is implemented in the `validate_api_key` function in `utils.py`:

```python
def validate_api_key(provided_key, expected_key):
    """Validate API key using constant time comparison to prevent timing attacks"""
    if not expected_key or not provided_key:
        return False
    
    # Use constant time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(provided_key, expected_key)
```

Rate limiting uses an in-memory cache with time-based expiration, implemented in the `rate_limit` function in `utils.py`.
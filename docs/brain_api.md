# Brain Microservice API

The **Brain** is a standalone, stateless microservice that provides intelligent search and answer generation capabilities. It takes questions as input and returns accurate, cited answers based on your document corpus.

## Overview

The Brain microservice is designed with a single, clear purpose:

- **Input:** A user question
- **Output:** An accurate answer with a source citation

It has **no authentication**, **no login**, **no user tracking**, and **no session management**. It is a pure intelligence layer.

## Architecture

```
┌─────────────┐
│   Question  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Brain Service   │────▶ Azure Search (Searcher)
│                  │
│  POST /query     │────▶ Azure OpenAI (Reasoning Engine)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Answer + Source │
└──────────────────┘
```

The Brain consists of three internal components:

1. **Searcher:** Uses Azure AI Search to find relevant paragraphs from your documents.
2. **Reasoning Engine:** Sends the paragraph to GPT-4 and asks it to write a polite, accurate answer.
3. **API Endpoint:** The stateless REST interface that orchestrates the entire process.

## API Endpoints

### Health Check

**Endpoint:** `GET /health`

**Purpose:** Health check for load balancers and monitoring.

**Response:**

```json
{
  "status": "ok"
}
```

**Status Code:** `200 OK`

---

### Query (Main Endpoint)

**Endpoint:** `POST /query`

**Purpose:** Submit a question and get an answer with citations.

**Request Body:**

```json
{
  "query": "What is the torque setting for standard connections?"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The question to answer. Must not be empty. |

**Response (Success):**

**Status Code:** `200 OK`

```json
{
  "answer": "The torque is 5Nm for standard connections.",
  "citation": "Page 42",
  "source_documents": [
    {
      "id": "doc-1",
      "content": "For standard connections, apply a torque of 5Nm...",
      "sourcepage": "42"
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | The generated answer, grounded in the retrieved documents. |
| `citation` | string | Source reference (e.g., "Page 42"). |
| `source_documents` | array (optional) | Top 3 source documents used to generate the answer. |
| `source_documents[].id` | string | Document ID. |
| `source_documents[].content` | string | Excerpt from the document. |
| `source_documents[].sourcepage` | string | Page or section reference. |

---

### Error Responses

**Status Code:** `400 Bad Request`

Missing or invalid query:

```json
{
  "error": "Missing required field: 'query'",
  "code": 400
}
```

Empty query:

```json
{
  "error": "Query cannot be empty",
  "code": 400
}
```

Invalid JSON:

```json
{
  "error": "Invalid JSON in request body",
  "code": 400
}
```

**Status Code:** `500 Internal Server Error`

Service initialization failure:

```json
{
  "error": "Service not initialized",
  "code": 500
}
```

Processing error:

```json
{
  "error": "Error processing query: [details]",
  "code": 500
}
```

---

## Usage Examples

### cURL

```bash
# Basic query
curl -X POST "http://localhost:50505/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I reset the error?"}'

# With authentication (if deployed with security headers)
curl -X POST "http://localhost:50505/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"query": "What is the maximum operating temperature?"}'
```

### Python

```python
import requests
import json

url = "http://localhost:50505/query"
headers = {"Content-Type": "application/json"}
payload = {"query": "What is the torque setting?"}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    result = response.json()
    print(f"Answer: {result['answer']}")
    print(f"Citation: {result['citation']}")
else:
    print(f"Error: {response.json()['error']}")
```

### JavaScript/TypeScript

```typescript
async function query(question: string) {
  const response = await fetch("http://localhost:50505/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query: question })
  });

  if (response.ok) {
    const data = await response.json();
    console.log("Answer:", data.answer);
    console.log("Citation:", data.citation);
    return data;
  } else {
    const error = await response.json();
    console.error("Error:", error.error);
  }
}

// Usage
query("How do I reset the error?");
```

---

## Code Structure

The Brain microservice is composed of five core files (all in `app/backend/`):

### **brain_app.py** - Main API Server
The Quart web application that handles HTTP requests:
- `GET /health` - Health check endpoint
- `POST /query` - Main query endpoint that receives questions and returns answers
- Startup initialization that loads configuration and sets up all Azure clients
- Error handling and response formatting

### **config_brain.py** - Configuration Management
Uses Pydantic for type-safe configuration:
- `BrainConfig` class that auto-loads from environment variables
- Validates required fields on startup
- Manages Azure Search, OpenAI, and server settings
- `load_config()` function to load and validate configuration

**Key environment variables managed:**
```bash
AZURE_SEARCH_SERVICE="your-service"
AZURE_SEARCH_INDEX="your-index"
AZURE_OPENAI_SERVICE="your-service"
AZURE_OPENAI_DEPLOYMENT="gpt-4"
AZURE_OPENAI_MODEL="gpt-4"
OPENAI_HOST="azure"  # or "openai", "azure_custom", "local"
BRAIN_HOST="0.0.0.0"
BRAIN_PORT="50505"
```

### **setup_brain.py** - Service Initialization
Wires up all Azure services on startup:
- `setup_brain_clients(config)` - Single function that takes a `BrainConfig` and returns all initialized clients
- Sets up Azure Search client (for document retrieval)
- Sets up Azure OpenAI client (for the reasoning engine)
- Initializes Prompt Manager (for Jinja2 templates)
- Creates Brain approach (RAG orchestrator)
- Optionally sets up knowledge base retrieval clients for agentic retrieval

### **models/brain_models.py** - Data Models
Dataclass definitions for request/response validation:
- `QueryRequest` - Input: `{"query": "..."}`
- `QueryResponse` - Output: `{"answer": "...", "citation": "...", "source_documents": [...]}`
- `QueryError` - Error response: `{"error": "message", "code": 500}`

### **tests/test_brain_api.py** - Automated Tests
Comprehensive test suite:
- Health check validation
- Input validation (missing/empty queries)
- Successful query processing with mocked services
- No sources found scenarios
- Source document inclusion
- Error handling

---

## Setup and Deployment

### Local Development - Quick Start (Free)

**Option 1: Stubbed Mode (Fastest)**

Run with a local mock endpoint - no API keys needed:

```bash
cd app/backend

# Copy example config
cp ../../.env.example .env

# Start a local LLM server using Ollama (install from ollama.com first)
ollama run mistral

# In another terminal, run Brain service
python brain_app.py
```

**Option 2: Hugging Face (Free API)**

```bash
# Get free token from https://huggingface.co/settings/tokens

export AZURE_SEARCH_SERVICE="your-search-service"
export AZURE_SEARCH_INDEX="your-index"
export OPENAI_HOST=openai
export OPENAI_API_KEY=hf_YOUR_HUGGING_FACE_TOKEN

python brain_app.py
```

**Option 3: Azure OpenAI (Production)**

```bash
export AZURE_SEARCH_SERVICE="your-search-service"
export AZURE_SEARCH_INDEX="your-index"
export AZURE_OPENAI_SERVICE="your-openai-service"
export AZURE_OPENAI_DEPLOYMENT="gpt-4"
export AZURE_OPENAI_MODEL="gpt-4"

python brain_app.py
```

The service will start on `http://localhost:50505` by default.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_SEARCH_SERVICE` | Yes | - | Azure Search service name |
| `AZURE_SEARCH_INDEX` | Yes | - | Search index name |
| `OPENAI_HOST` | No | azure | LLM provider: `azure`, `openai`, `azure_custom`, `local` |
| `AZURE_OPENAI_SERVICE` | Conditional | - | Required if OPENAI_HOST=azure |
| `AZURE_OPENAI_DEPLOYMENT` | Conditional | - | Required if OPENAI_HOST=azure |
| `AZURE_OPENAI_MODEL` | Conditional | gpt-4 | Model name (if using Azure) |
| `OPENAI_API_KEY` | Conditional | - | API key for non-Azure OpenAI or Hugging Face |
| `OPENAI_ENDPOINT` | Conditional | - | Custom endpoint for `local` mode |
| `AZURE_OPENAI_API_KEY_OVERRIDE` | No | - | Override API key for Azure |
| `BRAIN_HOST` | No | 0.0.0.0 | Host to bind to |
| `BRAIN_PORT` | No | 50505 | Port to run on |
| `BRAIN_DEBUG` | No | false | Debug mode (true/false) |
| `USE_AGENTIC_KNOWLEDGEBASE` | No | false | Enable agentic retrieval (true/false) |
| `USE_WEB_SOURCE` | No | false | Enable web source in retrieval (true/false) |
| `USE_SHAREPOINT_SOURCE` | No | false | Enable SharePoint source in retrieval (true/false) |

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
# Build
docker build -t brain-service:latest -f app/backend/Dockerfile.brain .

# Run with Hugging Face (free)
docker run -p 50505:50505 \
  -e AZURE_SEARCH_SERVICE="your-service" \
  -e AZURE_SEARCH_INDEX="your-index" \
  -e OPENAI_HOST=openai \
  -e OPENAI_API_KEY=hf_YOUR_TOKEN \
  brain-service:latest

# Run with Azure OpenAI
docker run -p 50505:50505 \
  -e AZURE_SEARCH_SERVICE="your-service" \
  -e AZURE_SEARCH_INDEX="your-index" \
  -e AZURE_OPENAI_SERVICE="your-openai" \
  -e AZURE_OPENAI_DEPLOYMENT="gpt-4" \
  -e AZURE_OPENAI_MODEL="gpt-4" \
  brain-service:latest
```

### Azure Deployment (azd)

To deploy as part of the Enterprise Knowledge Hub:

```bash
azd up
```

The Brain service will be deployed as a separate API endpoint alongside the main application.

---

## Features

✅ **Stateless:** Every request is independent. No session state needed.

✅ **No Authentication Required:** Call the API directly from client or frontend.

✅ **Fast:** Optimized for quick question-answer cycles.

✅ **Accurate:** Answers are grounded in your document corpus.

✅ **Cited:** Every answer includes the source page/document.

✅ **Scalable:** Stateless design allows horizontal scaling.

---

## Limitations

- **Single Question:** Each request answers one question. Multi-turn conversations are not supported in this version.
- **No Memory:** The Brain doesn't remember previous questions. Every query is independent.
- **No User Tracking:** No audit logs or user activity tracking.
- **Synchronous:** Responses are returned once the answer is generated (no streaming in this version).

---

## Performance Considerations

- **Latency:** Typically 2-5 seconds per query (includes search + LLM reasoning).
- **Throughput:** Can handle multiple concurrent requests.
- **Cost:** Each query incurs:
  - One Azure Search query
  - One Azure OpenAI API call (completion)
  - One Azure OpenAI API call for embeddings (if vector search is enabled)

---

## Troubleshooting

### Error: "Service not initialized"

**Cause:** The Brain service failed to initialize on startup.

**Solution:** Check logs and ensure all required environment variables are set:

```bash
echo $AZURE_SEARCH_SERVICE
echo $AZURE_OPENAI_SERVICE
```

### Error: "Missing required field: 'query'"

**Cause:** The request body doesn't include a `query` field.

**Solution:** Ensure your JSON includes the query field:

```json
{
  "query": "Your question here"
}
```

### No relevant sources found

**Cause:** The search index doesn't have documents matching the query.

**Solution:**
1. Verify documents are indexed in Azure Search.
2. Check the search index contains the expected content.
3. Try a simpler query or check document ingestion.

---

## Integration Examples

### With a Frontend App

```typescript
// In your frontend (React, Vue, etc.)
async function askBrain(question: string) {
  const response = await fetch(process.env.REACT_APP_BRAIN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: question })
  });

  if (response.ok) {
    return response.json(); // { answer, citation, source_documents }
  } else {
    throw new Error(await response.text());
  }
}
```

### With a Chatbot

```python
# In your chatbot logic
def get_answer_from_brain(user_message: str) -> dict:
    response = requests.post(
        "http://brain-service:50505/query",
        json={"query": user_message}
    )
    return response.json()
```

---

## Support & Contribution

For issues, feature requests, or contributions, please refer to the main [Enterprise Knowledge Hub](https://github.com/Arrryyy/Enterprise-Knowledge-Hub) repository.

---

## License

See the main repository for licensing information.

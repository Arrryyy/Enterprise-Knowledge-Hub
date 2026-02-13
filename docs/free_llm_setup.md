# Using the Brain Microservice with Free LLMs

You can run the Brain microservice without any Azure keys or paid services. This guide explains how to use free or local LLMs.

## Option 1: Ollama (Recommended for Local Development)

**Ollama** lets you run open-source LLMs locally on your machine, completely free.

### Prerequisites
- Docker, or native installation from [ollama.com](https://ollama.com)

### Setup Steps

1. **Install and start Ollama:**

   Option A - Using Docker:
   ```bash
   docker run -d -p 11434:11434 --name ollama ollama/ollama
   ```

   Option B - Native:
   ```bash
   # Download from ollama.com and run
   ollama serve
   ```

2. **Pull a model** (in another terminal):
   ```bash
   ollama pull mistral
   # or try: mistral, llama2, neural-chat, dolphin-mixtral, etc.
   ```

3. **Set environment variables:**
   ```bash
   export AZURE_SEARCH_SERVICE=test-search
   export AZURE_SEARCH_INDEX=test-index
   export OPENAI_HOST=local
   export OPENAI_ENDPOINT=http://localhost:11434/v1
   ```

4. **Run the Brain microservice:**
   ```bash
   cd app/backend
   python brain_app.py
   ```

5. **Test it:**
   ```bash
   curl -X POST http://localhost:50505/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is this document about?"}'
   ```

### Model Recommendations

For the Brain microservice, we recommend:

| Model | Size | Speed | Quality | Command |
|-------|------|-------|---------|---------|
| Mistral | 7.4B | Fast | Good | `ollama pull mistral` |
| Neural-Chat | 7.3B | Fast | Good | `ollama pull neural-chat` |
| Llama 2 | 7B | Fast | Good | `ollama pull llama2` |
| Dolphin Mixtral | 26.4B | Medium | Very Good | `ollama pull dolphin-mixtral` |
| Openchat | 7.3B | Fast | Good | `ollama pull openchat` |

**For your first test**, start with `mistral` - it's fast and produces good results.

---

## Option 2: Hugging Face (Free API with Token)

**Hugging Face** offers free API access to hosted models. Great if you don't want to run a local server.

### Setup Steps

1. **Get a free token:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new access token (can be read-only)

2. **Set environment variables:**
   ```bash
   export AZURE_SEARCH_SERVICE=test-search
   export AZURE_SEARCH_INDEX=test-index
   export OPENAI_HOST=openai
   export OPENAI_API_KEY=hf_YOUR_TOKEN_HERE
   ```

3. **Run the Brain microservice:**
   ```bash
   cd app/backend
   python brain_app.py
   ```

### Important Notes

- Free tier has rate limits (~10 requests/minute for some models)
- Some models may be slower due to server load
- Works great for testing and prototyping
- Upgrade to paid plans for production use

---

## Option 3: vLLM (Self-Hosted, Very Fast)

**vLLM** is an optimized serving engine for LLMs. Great for production-like local testing.

### Setup Steps

1. **Install vLLM** (requires GPU or significant CPU):
   ```bash
   pip install vllm
   ```

2. **Start a local vLLM server:**
   ```bash
   python -m vllm.entrypoints.openai.api_server --model mistralai/Mistral-7B-Instruct-v0.1
   ```

3. **Set environment variables:**
   ```bash
   export AZURE_SEARCH_SERVICE=test-search
   export AZURE_SEARCH_INDEX=test-index
   export OPENAI_HOST=local
   export OPENAI_ENDPOINT=http://localhost:8000/v1
   ```

4. **Run the Brain microservice:**
   ```bash
   cd app/backend
   python brain_app.py
   ```

---

## Option 4: Using with Test Data

If you don't have Azure Search configured yet, you can use a stub search client for testing:

### Create a Test Index

1. **Create a mock index** in your local search service or use Azure Free tier

2. **Sample documents to add:**
   ```json
   {
     "id": "1",
     "content": "The torque specification for the main shaft is 5 Nm.",
     "metadata_storage_path": "technical_manual.pdf"
   }
   ```

3. **Test the Brain API:**
   ```bash
   curl -X POST http://localhost:50505/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the torque setting?"}'
   ```

---

## Performance Comparison

| Setup | Startup | First Query | Ongoing Queries | Accuracy | Cost |
|-------|---------|-------------|-----------------|----------|------|
| Ollama (Mistral) | 5-10s | 2-5s | 2-5s per query | Good | Free |
| Ollama (Larger) | 10-15s | 5-10s | 5-10s per query | Very Good | Free |
| Hugging Face | 1-2s | 5-30s | 5-30s per query | Good | Free |
| vLLM (GPU) | 10-20s | 1-3s | 1-3s per query | Very Good | Free |
| Azure OpenAI | 1-2s | 0.5-2s | 0.5-2s per query | Excellent | Paid |

---

## Troubleshooting

### Ollama Connection Refused
```bash
# Make sure Ollama is running
ollama serve

# Or check if it's running on Docker
docker ps | grep ollama

# Test the endpoint directly
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "test"
}'
```

### Hugging Face Rate Limit
If you hit rate limits, either:
1. Wait a few seconds and retry
2. Upgrade to a paid plan
3. Use a local setup (Ollama or vLLM)

### Search Service Connection Issues
Set `AZURE_SEARCH_SERVICE=test-search` and we'll use test data internally (if implemented).

---

## Next Steps

Once you have the Brain API working with a free LLM:

1. **Add your own documents** to Azure Search
2. **Test with real queries** on your data
3. **Monitor performance** and adjust as needed
4. **Deploy to cloud** when ready (see main README)

See the [Brain API documentation](brain_api.md) for complete API details.

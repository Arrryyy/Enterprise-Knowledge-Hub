"""Configuration constants for the Brain microservice."""

# Core services
CONFIG_CREDENTIAL = "azure_credential"
CONFIG_OPENAI_CLIENT = "openai_client"
CONFIG_SEARCH_CLIENT = "search_client"
CONFIG_KNOWLEDGEBASE_CLIENT = "knowledgebase_client"
CONFIG_KNOWLEDGEBASE_CLIENT_WITH_WEB = "knowledgebase_client_with_web"
CONFIG_KNOWLEDGEBASE_CLIENT_WITH_SHAREPOINT = "knowledgebase_client_with_sharepoint"
CONFIG_KNOWLEDGEBASE_CLIENT_WITH_WEB_AND_SHAREPOINT = "knowledgebase_client_with_web_and_sharepoint"

# RAG/Search configuration
CONFIG_SEMANTIC_RANKER_DEPLOYED = "semantic_ranker_deployed"
CONFIG_QUERY_REWRITING_ENABLED = "query_rewriting_enabled"
CONFIG_VECTOR_SEARCH_ENABLED = "vector_search_enabled"
CONFIG_MULTIMODAL_ENABLED = "multimodal_enabled"

# Retrieval settings
CONFIG_DEFAULT_RETRIEVAL_REASONING_EFFORT = "default_retrieval_reasoning_effort"
CONFIG_AGENTIC_KNOWLEDGEBASE_ENABLED = "agentic_knowledgebase_enabled"
CONFIG_RAG_SEARCH_TEXT_EMBEDDINGS = "rag_search_text_embeddings"
CONFIG_RAG_SEARCH_IMAGE_EMBEDDINGS = "rag_search_image_embeddings"

# Optional: Web and SharePoint sources
CONFIG_WEB_SOURCE_ENABLED = "web_source_enabled"
CONFIG_SHAREPOINT_SOURCE_ENABLED = "sharepoint_source_enabled"

# Blob storage for embeddings/images
CONFIG_GLOBAL_BLOB_MANAGER = "global_blob_manager"

# Prompt management
CONFIG_PROMPT_MANAGER = "prompt_manager"

# Brain approach
CONFIG_BRAIN_APPROACH = "brain_approach"

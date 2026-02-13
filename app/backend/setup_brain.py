"""Setup utilities for the Brain microservice."""

import logging
import os
from typing import Optional

from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.knowledgebases.aio import KnowledgeBaseRetrievalClient
from openai import AsyncOpenAI

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.promptmanager import PromptManager
from prepdocslib.servicesetup import OpenAIHost, setup_openai_client, setup_search_info

logger = logging.getLogger("brain")


async def setup_brain_clients(
    search_service: str,
    search_index_name: str,
    openai_deployment: str,
    openai_model: str,
    openai_host: str = "azure",
    azure_credential: Optional[AsyncTokenCredential] = None,
    azure_openai_service: Optional[str] = None,
    azure_openai_api_key: Optional[str] = None,
    azure_openai_custom_url: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    search_key: Optional[str] = None,
    knowledgebase_enabled: bool = False,
    knowledgebase_name: Optional[str] = None,
    knowledgebase_model: Optional[str] = None,
    knowledgebase_deployment: Optional[str] = None,
    use_web_source: bool = False,
    use_sharepoint_source: bool = False,
    embedding_deployment: Optional[str] = None,
    query_language: str = "en-US",
    query_speller: str = "lexicon",
) -> tuple[SearchClient, AsyncOpenAI, PromptManager, Optional[ChatReadRetrieveReadApproach]]:
    """
    Set up all clients needed for the Brain microservice.

    Args:
        search_service: Name of the Azure Search service
        search_index_name: Name of the search index
        openai_deployment: Name of the OpenAI deployment
        openai_model: Model name (e.g., "gpt-4")
        openai_host: OpenAI host type ("azure", "openai", "azure_custom", "local")
        azure_credential: Azure credential for authentication
        azure_openai_service: Azure OpenAI service name
        azure_openai_api_key: Optional API key for Azure OpenAI
        azure_openai_custom_url: Custom URL for Azure OpenAI
        openai_api_key: API key for OpenAI (non-Azure)
        search_key: Optional search key
        knowledgebase_enabled: Whether to use agentic knowledge base retrieval
        knowledgebase_name: Name of the knowledge base (if agentic retrieval enabled)
        knowledgebase_model: Model for knowledge base
        knowledgebase_deployment: Deployment for knowledge base
        use_web_source: Whether to enable web source
        use_sharepoint_source: Whether to enable SharePoint source
        embedding_deployment: Deployment for embeddings
        query_language: Language for queries
        query_speller: Speller configuration

    Returns:
        Tuple of (search_client, openai_client, prompt_manager, brain_approach)
    """
    if azure_credential is None:
        logger.info("No credential provided, using AzureDeveloperCliCredential")
        azure_credential = AzureDeveloperCliCredential()

    # Set up OpenAI client
    logger.info(f"Setting up OpenAI client with host: {openai_host}")
    openai_client, azure_openai_endpoint = setup_openai_client(
        openai_host=OpenAIHost(openai_host),
        azure_credential=azure_credential,
        azure_openai_api_key=azure_openai_api_key,
        azure_openai_service=azure_openai_service,
        azure_openai_custom_url=azure_openai_custom_url,
        openai_api_key=openai_api_key,
    )

    # Set up search client
    logger.info(f"Setting up search client for {search_service}")
    search_info = setup_search_info(
        search_service=search_service,
        index_name=search_index_name,
        azure_credential=azure_credential,
        use_agentic_knowledgebase=knowledgebase_enabled,
        azure_openai_endpoint=azure_openai_endpoint,
        knowledgebase_name=knowledgebase_name,
        azure_openai_knowledgebase_deployment=knowledgebase_deployment,
        azure_openai_knowledgebase_model=knowledgebase_model,
    )

    search_client = SearchClient(
        endpoint=search_info.endpoint,
        index_name=search_info.index_name,
        credential=search_info.credential,
    )

    # Set up knowledge base retrieval clients if enabled
    knowledgebase_client = None
    knowledgebase_client_with_web = None
    knowledgebase_client_with_sharepoint = None
    knowledgebase_client_with_web_and_sharepoint = None

    if knowledgebase_enabled and search_info.knowledgebase_name:
        logger.info("Setting up knowledge base retrieval clients")
        knowledgebase_client = KnowledgeBaseRetrievalClient(
            endpoint=search_info.endpoint,
            knowledgebase_name=search_info.knowledgebase_name,
            credential=search_info.credential,
        )

        if use_web_source or use_sharepoint_source:
            knowledgebase_client_with_web = KnowledgeBaseRetrievalClient(
                endpoint=search_info.endpoint,
                knowledgebase_name=search_info.knowledgebase_name,
                credential=search_info.credential,
            )
            knowledgebase_client_with_sharepoint = KnowledgeBaseRetrievalClient(
                endpoint=search_info.endpoint,
                knowledgebase_name=search_info.knowledgebase_name,
                credential=search_info.credential,
            )
            knowledgebase_client_with_web_and_sharepoint = KnowledgeBaseRetrievalClient(
                endpoint=search_info.endpoint,
                knowledgebase_name=search_info.knowledgebase_name,
                credential=search_info.credential,
            )

    # Set up prompt manager
    logger.info("Setting up prompt manager")
    prompt_manager = PromptManager(prompt_dir=os.path.join(os.path.dirname(__file__), "approaches", "prompts"))

    # Create the Brain approach
    brain_approach = ChatReadRetrieveReadApproach(
        search_client=search_client,
        search_index_name=search_index_name,
        knowledgebase_model=knowledgebase_model,
        knowledgebase_deployment=knowledgebase_deployment,
        knowledgebase_client=knowledgebase_client,
        knowledgebase_client_with_web=knowledgebase_client_with_web,
        knowledgebase_client_with_sharepoint=knowledgebase_client_with_sharepoint,
        knowledgebase_client_with_web_and_sharepoint=knowledgebase_client_with_web_and_sharepoint,
        openai_client=openai_client,
        chatgpt_model=openai_model,
        chatgpt_deployment=openai_deployment,
        embedding_deployment=embedding_deployment,
        query_language=query_language,
        query_speller=query_speller,
        prompt_manager=prompt_manager,
    )

    logger.info("Brain clients setup complete")
    return search_client, openai_client, prompt_manager, brain_approach

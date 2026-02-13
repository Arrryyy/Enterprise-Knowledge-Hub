"""Setup utilities for the Brain microservice."""

import logging
import os
from typing import TYPE_CHECKING, Optional

from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.knowledgebases.aio import KnowledgeBaseRetrievalClient
from openai import AsyncOpenAI

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.promptmanager import PromptManager
from prepdocslib.servicesetup import OpenAIHost, setup_openai_client, setup_search_info

if TYPE_CHECKING:
    from config_brain import BrainConfig

logger = logging.getLogger("brain_setup")


async def setup_brain_clients(
    config: "BrainConfig",
    azure_credential: Optional[AsyncTokenCredential] = None,
) -> tuple[SearchClient, AsyncOpenAI, PromptManager, Optional[ChatReadRetrieveReadApproach]]:
    """
    Set up all clients needed for the Brain microservice.

    Args:
        config: BrainConfig instance with all configuration
        azure_credential: Azure credential for authentication (optional, will use default if not provided)

    Returns:
        Tuple of (search_client, openai_client, prompt_manager, brain_approach)
    """
    if azure_credential is None:
        logger.info("No credential provided, using AzureDeveloperCliCredential")
        azure_credential = AzureDeveloperCliCredential()

    # Set up OpenAI client
    logger.info(f"Setting up OpenAI client with host: {config.openai_host}")
    openai_client, azure_openai_endpoint = setup_openai_client(
        openai_host=OpenAIHost(config.openai_host),
        azure_credential=azure_credential,
        azure_openai_api_key=config.azure_openai_api_key,
        azure_openai_service=config.azure_openai_service,
        azure_openai_custom_url=config.azure_openai_custom_url,
        openai_api_key=config.openai_api_key,
    )

    # Set up search client
    logger.info(f"Setting up search client for {config.search_service}")
    search_info = setup_search_info(
        search_service=config.search_service,
        index_name=config.search_index,
        azure_credential=azure_credential,
        use_agentic_knowledgebase=config.use_agentic_knowledgebase,
        azure_openai_endpoint=azure_openai_endpoint,
        knowledgebase_name=config.knowledgebase_name,
        azure_openai_knowledgebase_deployment=config.knowledgebase_deployment,
        azure_openai_knowledgebase_model=config.knowledgebase_model,
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

    if config.use_agentic_knowledgebase and search_info.knowledgebase_name:
        logger.info("Setting up knowledge base retrieval clients")
        knowledgebase_client = KnowledgeBaseRetrievalClient(
            endpoint=search_info.endpoint,
            knowledgebase_name=search_info.knowledgebase_name,
            credential=search_info.credential,
        )

        if config.use_web_source or config.use_sharepoint_source:
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
        search_index_name=config.search_index,
        knowledgebase_model=config.knowledgebase_model,
        knowledgebase_deployment=config.knowledgebase_deployment,
        knowledgebase_client=knowledgebase_client,
        knowledgebase_client_with_web=knowledgebase_client_with_web,
        knowledgebase_client_with_sharepoint=knowledgebase_client_with_sharepoint,
        knowledgebase_client_with_web_and_sharepoint=knowledgebase_client_with_web_and_sharepoint,
        openai_client=openai_client,
        chatgpt_model=config.openai_model,
        chatgpt_deployment=config.openai_deployment,
        embedding_deployment=config.embedding_deployment,
        query_language=config.query_language,
        query_speller=config.query_speller,
        prompt_manager=prompt_manager,
    )

    logger.info("Brain clients setup complete")
    return search_client, openai_client, prompt_manager, brain_approach

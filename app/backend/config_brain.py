"""Configuration for the Brain microservice."""

import os
from typing import Optional

from pydantic import BaseModel, Field


class BrainConfig(BaseModel):
    """Configuration for the Brain microservice.

    All fields can be set via environment variables or constructor parameters.
    Environment variable names follow the AZURE_* and OPENAI_* conventions.
    """

    # Azure Search configuration
    search_service: str = Field(
        default_factory=lambda: os.getenv("AZURE_SEARCH_SERVICE", ""), description="Name of the Azure Search service"
    )
    search_index: str = Field(
        default_factory=lambda: os.getenv("AZURE_SEARCH_INDEX", ""), description="Name of the search index"
    )
    search_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_SEARCH_SERVICE_KEY"), description="Optional API key for Azure Search"
    )

    # Azure OpenAI configuration
    openai_host: str = Field(
        default_factory=lambda: os.getenv("OPENAI_HOST", "azure"),
        description="OpenAI host type (azure, openai, azure_custom, local)",
    )
    openai_deployment: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT", ""), description="Azure OpenAI deployment name"
    )
    openai_model: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_MODEL", "gpt-4"), description="OpenAI model name (e.g., gpt-4)"
    )
    azure_openai_service: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_SERVICE"), description="Azure OpenAI service name"
    )
    azure_openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY_OVERRIDE"),
        description="Optional API key for Azure OpenAI",
    )
    azure_openai_custom_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_CUSTOM_URL"),
        description="Custom URL for Azure OpenAI (for network isolation)",
    )
    openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"), description="API key for non-Azure OpenAI"
    )

    # Knowledge base / Agentic retrieval configuration
    use_agentic_knowledgebase: bool = Field(
        default_factory=lambda: os.getenv("USE_AGENTIC_KNOWLEDGEBASE", "false").lower() == "true",
        description="Enable agentic knowledge base retrieval",
    )
    knowledgebase_name: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_SEARCH_KNOWLEDGEBASE"), description="Name of the knowledge base"
    )
    knowledgebase_model: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_KNOWLEDGEBASE_MODEL"),
        description="Model for knowledge base retrieval",
    )
    knowledgebase_deployment: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_KNOWLEDGEBASE_DEPLOYMENT"),
        description="Deployment for knowledge base retrieval",
    )

    # Optional retrieval sources
    use_web_source: bool = Field(
        default_factory=lambda: os.getenv("USE_WEB_SOURCE", "false").lower() == "true",
        description="Enable web source in retrieval",
    )
    use_sharepoint_source: bool = Field(
        default_factory=lambda: os.getenv("USE_SHAREPOINT_SOURCE", "false").lower() == "true",
        description="Enable SharePoint source in retrieval",
    )

    # Embeddings configuration
    embedding_deployment: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"), description="Deployment for embeddings"
    )

    # Query configuration
    query_language: str = Field(default="en-US", description="Language for queries")
    query_speller: str = Field(default="lexicon", description="Speller configuration")

    # API server configuration
    brain_host: str = Field(
        default_factory=lambda: os.getenv("BRAIN_HOST", "0.0.0.0"), description="Host to bind the Brain API to"
    )
    brain_port: int = Field(
        default_factory=lambda: int(os.getenv("BRAIN_PORT", "50505")), description="Port for the Brain API"
    )
    brain_debug: bool = Field(
        default_factory=lambda: os.getenv("BRAIN_DEBUG", "false").lower() == "true", description="Enable debug mode"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False

    def validate_required_fields(self) -> None:
        """Validate that all required fields are set.

        Raises:
            ValueError: If any required field is missing or empty.
        """
        required_fields = [
            ("search_service", self.search_service),
            ("search_index", self.search_index),
            ("openai_deployment", self.openai_deployment),
            ("openai_model", self.openai_model),
        ]

        if self.openai_host == "azure" or self.openai_host == "azure_custom":
            required_fields.append(("azure_openai_service", self.azure_openai_service))
        elif self.openai_host == "openai":
            required_fields.append(("openai_api_key", self.openai_api_key))

        missing = [name for name, value in required_fields if not value]
        if missing:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing)}. "
                f"Set these as environment variables or pass them to BrainConfig()."
            )


def load_config() -> BrainConfig:
    """Load and validate Brain configuration from environment.

    Returns:
        Validated BrainConfig instance.

    Raises:
        ValueError: If required fields are missing.
    """
    config = BrainConfig()
    config.validate_required_fields()
    return config

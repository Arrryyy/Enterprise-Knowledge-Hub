"""Request and response models for the Brain microservice API."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryRequest:
    """Request to the Brain's /query endpoint.

    Attributes:
        query: The user's question to search for and answer.
    """

    query: str


@dataclass
class QueryResponse:
    """Response from the Brain's /query endpoint.

    Attributes:
        answer: The generated answer based on retrieved documents.
        citation: Source citation (e.g., "Page 42" or "Document ID: xyz").
        source_documents: Optional list of source document snippets used for the answer.
    """

    answer: str
    citation: str
    source_documents: Optional[list[dict]] = None


@dataclass
class QueryError:
    """Error response from the Brain's /query endpoint.

    Attributes:
        error: Error message describing what went wrong.
        code: HTTP status code.
    """

    error: str
    code: int

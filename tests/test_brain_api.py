"""Tests for the Brain microservice API."""

import sys
from pathlib import Path
from unittest import mock

import pytest
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, Choice

# Add app/backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from brain_app import create_brain_app


@pytest.fixture
async def brain_client():
    """Create a test client for the Brain app."""
    app = create_brain_app()

    # Mock the setup_storage to avoid actual Azure calls
    async def mock_setup():
        pass

    app.before_serving_funcs = app.before_serving_funcs[:]  # Clone to avoid side effects
    app.before_serving_funcs.clear()
    app.before_serving_funcs.append(mock_setup)

    async with app.test_client() as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_health_check(brain_client):
    """Test the health check endpoint."""
    response = await brain_client.get("/health")
    assert response.status_code == 200
    data = await response.get_json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_query_missing_field(brain_client):
    """Test /query endpoint with missing query field."""
    response = await brain_client.post("/query", json={})
    assert response.status_code == 400
    data = await response.get_json()
    assert "query" in data.get("error", "").lower()


@pytest.mark.asyncio
async def test_query_empty_query(brain_client):
    """Test /query endpoint with empty query."""
    response = await brain_client.post("/query", json={"query": ""})
    assert response.status_code == 400
    data = await response.get_json()
    assert "empty" in data.get("error", "").lower()


@pytest.mark.asyncio
async def test_query_invalid_json(brain_client):
    """Test /query endpoint with invalid JSON."""
    response = await brain_client.post("/query", data="not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    data = await response.get_json()
    assert "json" in data.get("error", "").lower()


@pytest.mark.asyncio
async def test_query_success_with_mocked_approach(brain_client):
    """Test successful query with mocked Brain approach."""
    from approaches.approach import DataPoints, ExtraInfo

    mock_approach = mock.AsyncMock()
    mock_data_points = DataPoints(
        data=[
            {"id": "test-doc-1", "content": "The torque setting is 5Nm for standard connections.", "sourcepage": "42"}
        ],
        thoughts=[],
    )
    mock_extra_info = ExtraInfo(data=mock_data_points.data, thoughts=[])
    mock_approach.run_search_approach.return_value = mock_extra_info

    # Mock the OpenAI client
    mock_openai = mock.AsyncMock()
    mock_completion = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content="The torque is 5Nm."),
                finish_reason="stop",
            )
        ],
        usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    mock_openai.chat.completions.create.return_value = mock_completion

    # Patch the config
    with mock.patch.dict(
        brain_client.application.config, {"brain_approach": mock_approach, "openai_client": mock_openai}
    ):
        response = await brain_client.post("/query", json={"query": "What is the torque setting?"})

        assert response.status_code == 200
        data = await response.get_json()
        assert "answer" in data
        assert "citation" in data
        assert "Page 42" in data["citation"]


@pytest.mark.asyncio
async def test_query_no_sources_found(brain_client):
    """Test query when no sources are found."""
    from approaches.approach import ExtraInfo

    mock_approach = mock.AsyncMock()
    mock_extra_info = ExtraInfo(data=[], thoughts=[])
    mock_approach.run_search_approach.return_value = mock_extra_info

    with mock.patch.dict(brain_client.application.config, {"brain_approach": mock_approach}):
        response = await brain_client.post("/query", json={"query": "What is the meaning of life?"})

        assert response.status_code == 200
        data = await response.get_json()
        assert "could not find" in data["answer"].lower()
        assert "No sources found" in data["citation"]


@pytest.mark.asyncio
async def test_query_with_source_documents(brain_client):
    """Test that source documents are included in response."""
    from approaches.approach import DataPoints, ExtraInfo

    mock_approach = mock.AsyncMock()
    mock_data_points = DataPoints(
        data=[
            {"id": "doc-1", "content": "First source", "sourcepage": "10"},
            {"id": "doc-2", "content": "Second source", "sourcepage": "20"},
        ],
        thoughts=[],
    )
    mock_extra_info = ExtraInfo(data=mock_data_points.data, thoughts=[])
    mock_approach.run_search_approach.return_value = mock_extra_info

    mock_openai = mock.AsyncMock()
    mock_completion = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            Choice(index=0, message=ChatCompletionMessage(role="assistant", content="The answer"), finish_reason="stop")
        ],
        usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    mock_openai.chat.completions.create.return_value = mock_completion

    with mock.patch.dict(
        brain_client.application.config, {"brain_approach": mock_approach, "openai_client": mock_openai}
    ):
        response = await brain_client.post("/query", json={"query": "Test query"})

        assert response.status_code == 200
        data = await response.get_json()
        assert "source_documents" in data
        assert len(data["source_documents"]) <= 3  # Should be limited to top 3


@pytest.mark.asyncio
async def test_query_not_initialized(brain_client):
    """Test query when Brain approach is not initialized."""
    with mock.patch.dict(brain_client.application.config, {"brain_approach": None}):
        response = await brain_client.post("/query", json={"query": "Test query"})

        assert response.status_code == 500
        data = await response.get_json()
        assert "not initialized" in data["error"].lower()


@pytest.mark.asyncio
async def test_query_different_source_pages(brain_client):
    """Test that source page information is correctly extracted."""
    from approaches.approach import DataPoints, ExtraInfo

    mock_approach = mock.AsyncMock()
    mock_data_points = DataPoints(
        data=[{"id": "test-doc", "content": "Some content", "sourcepage": "99"}], thoughts=[]  # Different page number
    )
    mock_extra_info = ExtraInfo(data=mock_data_points.data, thoughts=[])
    mock_approach.run_search_approach.return_value = mock_extra_info

    mock_openai = mock.AsyncMock()
    mock_completion = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            Choice(index=0, message=ChatCompletionMessage(role="assistant", content="Answer"), finish_reason="stop")
        ],
        usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    mock_openai.chat.completions.create.return_value = mock_completion

    with mock.patch.dict(
        brain_client.application.config, {"brain_approach": mock_approach, "openai_client": mock_openai}
    ):
        response = await brain_client.post("/query", json={"query": "Test"})

        assert response.status_code == 200
        data = await response.get_json()
        assert "Page 99" in data["citation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

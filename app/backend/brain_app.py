"""Brain microservice API.

A stateless API that provides intelligent search and answering capabilities
without authentication, login, or user-specific features.

The Brain microservice accepts questions and returns answers grounded in
the document corpus, with proper citations.
"""

import logging
import os

from azure.core.exceptions import AzureError
from quart import Quart, jsonify, request
from quart_cors import cors

from config_brain import (
    CONFIG_BRAIN_APPROACH,
    CONFIG_OPENAI_CLIENT,
    CONFIG_PROMPT_MANAGER,
    CONFIG_SEARCH_CLIENT,
)
from load_azd_env import load_azd_env
from models.brain_models import QueryError, QueryResponse
from setup_brain import setup_brain_clients

logger = logging.getLogger("brain_api")


def create_brain_app() -> Quart:
    """Create and configure the Brain microservice Quart application."""
    app = Quart(__name__)
    app = cors(app, allow_origin="*")  # Allow any origin for stateless API

    @app.before_serving
    async def setup_storage():
        """Initialize and store clients in app config on startup."""
        logger.info("Initializing Brain microservice...")
        try:
            search_client, openai_client, prompt_manager, brain_approach = await setup_brain_clients(
                search_service=os.getenv("AZURE_SEARCH_SERVICE", ""),
                search_index_name=os.getenv("AZURE_SEARCH_INDEX", ""),
                openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
                openai_model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                openai_host=os.getenv("OPENAI_HOST", "azure"),
                azure_openai_service=os.getenv("AZURE_OPENAI_SERVICE"),
                azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY_OVERRIDE"),
                azure_openai_custom_url=os.getenv("AZURE_OPENAI_CUSTOM_URL"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                search_key=os.getenv("AZURE_SEARCH_SERVICE_KEY"),
                knowledgebase_enabled=os.getenv("USE_AGENTIC_KNOWLEDGEBASE", "false").lower() == "true",
                knowledgebase_name=os.getenv("AZURE_SEARCH_KNOWLEDGEBASE", ""),
                knowledgebase_model=os.getenv("AZURE_OPENAI_KNOWLEDGEBASE_MODEL"),
                knowledgebase_deployment=os.getenv("AZURE_OPENAI_KNOWLEDGEBASE_DEPLOYMENT"),
                use_web_source=os.getenv("USE_WEB_SOURCE", "false").lower() == "true",
                use_sharepoint_source=os.getenv("USE_SHAREPOINT_SOURCE", "false").lower() == "true",
                embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            )

            app.config[CONFIG_SEARCH_CLIENT] = search_client
            app.config[CONFIG_OPENAI_CLIENT] = openai_client
            app.config[CONFIG_PROMPT_MANAGER] = prompt_manager
            app.config[CONFIG_BRAIN_APPROACH] = brain_approach

            logger.info("Brain microservice initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Brain microservice: {e}")
            raise

    @app.route("/health", methods=["GET"])
    async def health_check():
        """Health check endpoint for load balancers."""
        return jsonify({"status": "ok"}), 200

    @app.route("/query", methods=["POST"])
    async def query():
        """
        Query endpoint for the Brain microservice.

        Request body (JSON):
            {
                "query": "Your question here"
            }

        Response (JSON):
            {
                "answer": "The answer to your question",
                "citation": "Source reference (e.g., Page 42)"
            }

        Returns:
            200: Success with answer and citation
            400: Bad request (missing query)
            500: Internal server error
        """
        try:
            body = await request.get_json()
        except Exception as e:
            logger.warning(f"Invalid JSON in request: {e}")
            return jsonify(QueryError(error="Invalid JSON in request body", code=400).__dict__), 400

        if not body or "query" not in body:
            return jsonify(QueryError(error="Missing required field: 'query'", code=400).__dict__), 400

        user_query = body.get("query", "").strip()
        if not user_query:
            return jsonify(QueryError(error="Query cannot be empty", code=400).__dict__), 400

        try:
            brain_approach = app.config.get(CONFIG_BRAIN_APPROACH)
            if not brain_approach:
                logger.error("Brain approach not initialized")
                return jsonify(QueryError(error="Service not initialized", code=500).__dict__), 500

            # Format the query as a message for the approach
            messages = [{"role": "user", "content": user_query}]

            # Run the search approach to get context
            search_results = await brain_approach.run_search_approach(
                messages=messages,
                overrides={
                    "retrieval_mode": "hybrid",
                    "semantic_ranker": True,
                    "semantic_captions": True,
                    "query_rewriting": True,
                    "top": 5,
                    "minimum_search_score": 0.0,
                    "minimum_reranker_score": 0.0,
                },
                auth_claims={},  # No auth claims needed for Brain
            )

            # Extract answer from the approach response
            # The run_search_approach returns an ExtraInfo object with data_points
            data_points = search_results.data_points

            if not data_points.data:
                answer = "I could not find relevant information to answer your question."
                citation = "No sources found"
            else:
                # Use the first data point's content as the grounding text
                first_source = data_points.data[0]
                source_content = (
                    first_source.get("content", "") if isinstance(first_source, dict) else str(first_source)
                )
                source_page = first_source.get("sourcepage", "Unknown") if isinstance(first_source, dict) else "Unknown"

                # Generate answer using GPT-4 with the retrieved context
                openai_client = app.config.get(CONFIG_OPENAI_CLIENT)
                openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
                openai_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")

                system_prompt = f"""You are a helpful assistant that answers questions based on the provided context.
Always provide accurate, concise answers grounded only in the provided context.
Do not make up or hallucinate information.
If the context does not contain information needed to answer the question, say so clearly.

Context:
{source_content}"""

                response = await openai_client.chat.completions.create(
                    model=openai_deployment or openai_model,
                    temperature=0.7,
                    max_tokens=500,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_query}],
                )

                answer = response.choices[0].message.content
                citation = f"Page {source_page}"

            return (
                jsonify(
                    QueryResponse(
                        answer=answer,
                        citation=citation,
                        source_documents=[d for d in data_points.data[:3]] if data_points.data else None,
                    ).__dict__
                ),
                200,
            )

        except AzureError as e:
            logger.error(f"Azure service error: {e}")
            return jsonify(QueryError(error=f"Azure service error: {str(e)}", code=500).__dict__), 500
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return jsonify(QueryError(error=f"Error processing query: {str(e)}", code=500).__dict__), 500

    return app


def main():
    """Entry point for running the Brain microservice."""
    # Load environment variables from azd
    load_azd_env()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create the app
    app = create_brain_app()

    # Run the app
    host = os.getenv("BRAIN_HOST", "0.0.0.0")
    port = int(os.getenv("BRAIN_PORT", "50505"))
    debug = os.getenv("BRAIN_DEBUG", "false").lower() == "true"

    logger.info(f"Starting Brain microservice on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()

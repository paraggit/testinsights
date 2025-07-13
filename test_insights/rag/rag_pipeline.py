"""Retrieval Augmented Generation pipeline for ReportPortal queries."""

import json

import structlog

from test_insights.data_sync.storage.chromadb_client import ChromaDBClient
from test_insights.llm.providers.base import Message
from test_insights.llm.query_processor import QueryProcessor

logger = structlog.get_logger(__name__)


class RAGPipeline:
    """RAG pipeline for natural language querying of ReportPortal data."""

    def __init__(
        self,
        llm_provider,
        storage_client=None,
        query_processor=None,
    ):
        self.llm_provider = llm_provider
        self.storage_client = storage_client or ChromaDBClient()
        self.query_processor = query_processor or QueryProcessor()

    async def query(
        self,
        query,
        n_results=20,
        include_raw_results=False,
        stream=False,
    ):
        """
        Process a natural language query using RAG.

        Args:
            query: Natural language query
            n_results: Number of documents to retrieve
            include_raw_results: Whether to include raw search results
            stream: Whether to stream the response

        Returns:
            Dictionary with response and metadata
        """
        logger.info("Processing query", query=query)

        analysis = self.query_processor.analyze_query(query)
        logger.debug("Query analysis", analysis=analysis)

        search_query = self.query_processor.build_search_query(analysis)

        where_clause = {}
        if analysis["entity_types"]:
            where_clause["entity_type"] = {"$in": analysis["entity_types"]}
        if analysis["status_filter"]:
            where_clause["status"] = {"$in": analysis["status_filter"]}

        search_results = await self.storage_client.query(
            query_text=search_query,
            n_results=n_results,
            where=where_clause if where_clause else None,
        )

        logger.info(f"Retrieved {len(search_results)} documents")

        metrics = None
        if analysis["metrics_requested"]:
            metrics = self._calculate_metrics(search_results, analysis)

        messages = self._build_prompt(query, search_results, analysis, metrics)

        if stream:
            return {
                "response": self.llm_provider.generate_stream(messages),
                "analysis": analysis,
                "search_results": search_results if include_raw_results else None,
                "metrics": metrics,
            }
        else:
            response = await self.llm_provider.generate(messages)

            return {
                "response": response.content,
                "analysis": analysis,
                "search_results": search_results if include_raw_results else None,
                "metrics": metrics,
                "model": response.model,
                "usage": response.usage,
            }

    def _build_prompt(
        self,
        query,
        search_results,
        analysis,
        metrics=None,
    ):
        """Build the prompt for the LLM."""
        system_prompt = self.query_processor.build_system_prompt(analysis)

        context = self.llm_provider.format_context(search_results)

        if metrics:
            context += f"\n\n---\n\nCalculated Metrics:\n{json.dumps(metrics, indent=2)}"

        user_message = f"""Based on the following ReportPortal data,
                            please answer this question: {query}

Context:
{context}

Please provide a clear and helpful response based on the data provided."""

        return [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_message),
        ]

    def _calculate_metrics(
        self,
        search_results,
        analysis,
    ):
        """Calculate metrics from search results."""
        metrics = {
            "total_items": len(search_results),
            "by_status": {},
            "by_entity_type": {},
        }

        for result in search_results:
            metadata = result.get("metadata", {})
            status = metadata.get("status", "UNKNOWN")
            entity_type = metadata.get("entity_type", "unknown")

            metrics["by_status"][status] = metrics["by_status"].get(status, 0) + 1
            metrics["by_entity_type"][entity_type] = (
                metrics["by_entity_type"].get(entity_type, 0) + 1
            )

        if metrics["total_items"] > 0:
            metrics["status_percentages"] = {
                status: (count / metrics["total_items"]) * 100
                for status, count in metrics["by_status"].items()
            }

            failed_count = metrics["by_status"].get("FAILED", 0) + metrics["by_status"].get(
                "BROKEN", 0
            )
            passed_count = metrics["by_status"].get("PASSED", 0)

            if failed_count + passed_count > 0:
                metrics["failure_rate"] = (failed_count / (failed_count + passed_count)) * 100
                metrics["success_rate"] = (passed_count / (failed_count + passed_count)) * 100

        return metrics

    async def query_with_feedback(
        self,
        query,
        previous_response,
        feedback,
        n_results=20,
    ):
        """
        Process a follow-up query with feedback on the previous response.

        Args:
            query: Original query
            previous_response: Previous response from the system
            feedback: User feedback on what was missing or incorrect
            n_results: Number of documents to retrieve

        Returns:
            Dictionary with improved response
        """
        refined_query = f"{query} (User feedback: {feedback})"

        result = await self.query(refined_query, n_results=n_results)

        messages = [
            Message(
                role="system", content=self.query_processor.build_system_prompt(result["analysis"])
            ),
            Message(role="user", content=f"Original query: {query}"),
            Message(role="assistant", content=previous_response),
            Message(
                role="user",
                content=(
                    f"This response was incomplete. {feedback} Please provide an improved answer"
                    "based on the available data."
                ),
            ),
        ]

        response = await self.llm_provider.generate(messages)

        result["response"] = response.content
        result["refined"] = True

        return result

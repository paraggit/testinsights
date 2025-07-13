"""ChromaDB client for vector storage."""

import hashlib
import json
from datetime import datetime

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from test_insights.config.settings import settings
from test_insights.core.exceptions import StorageError

logger = structlog.get_logger(__name__)


class ChromaDBClient:
    """Client for ChromaDB vector database operations."""

    def __init__(self, persist_directory=None, collection_name=None):
        self.persist_directory = persist_directory or str(settings.chroma_persist_directory)
        self.collection_name = collection_name or settings.chroma_collection_name

        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function,
                metadata={
                    "description": "ReportPortal data for AI assistant",
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.error("Failed to create/get collection", error=str(e))
            raise StorageError(f"Failed to initialize collection: {e}")

    def _generate_id(self, entity_type, entity_data):
        if entity_type == "launch":
            key = f"{entity_type}:{entity_data.get('id')}"
        elif entity_type == "test_item":
            key = f"{entity_type}:{entity_data.get('id')}"
        elif entity_type == "log":
            key = f"{entity_type}:{entity_data.get('id')}"
        elif entity_type == "user":
            key = f"{entity_type}:{entity_data.get('userId', entity_data.get('id'))}"
        elif entity_type == "project":
            key = f"{entity_type}:{entity_data.get('projectName')}"
        elif entity_type == "filter":
            key = f"{entity_type}:{entity_data.get('id')}"
        elif entity_type == "dashboard":
            key = f"{entity_type}:{entity_data.get('id')}"
        else:
            content = json.dumps(entity_data, sort_keys=True)
            key = f"{entity_type}:{hashlib.md5(content.encode()).hexdigest()}"
        return key

    def _prepare_document(self, entity_type, entity_data, additional_metadata=None):
        text_content = self._extract_text_content(entity_type, entity_data)

        metadata = {
            "entity_type": entity_type,
            "entity_id": entity_data.get("id", ""),
            "created_at": datetime.utcnow().isoformat(),
            "last_modified": entity_data.get("lastModified", datetime.utcnow().isoformat()),
        }

        if entity_type == "launch":
            metadata.update(
                {
                    "launch_name": entity_data.get("name", ""),
                    "launch_number": entity_data.get("number", 0),
                    "status": entity_data.get("status", ""),
                    "mode": entity_data.get("mode", ""),
                    "owner": entity_data.get("owner", ""),
                }
            )
        elif entity_type == "test_item":
            metadata.update(
                {
                    "item_name": entity_data.get("name", ""),
                    "item_type": entity_data.get("type", ""),
                    "status": entity_data.get("status", ""),
                    "launch_id": entity_data.get("launchId", ""),
                }
            )
        elif entity_type == "log":
            metadata.update(
                {
                    "level": entity_data.get("level", ""),
                    "item_id": entity_data.get("itemId", ""),
                    "launch_id": entity_data.get("launchId", ""),
                }
            )

        if additional_metadata:
            metadata.update(additional_metadata)

        return {
            "id": self._generate_id(entity_type, entity_data),
            "document": text_content,
            "metadata": metadata,
            "entity_data": json.dumps(entity_data),
        }

    def _extract_text_content(self, entity_type, entity_data):
        text_parts = []

        if entity_type == "launch":
            text_parts.extend(
                [
                    f"Launch: {entity_data.get('name', '')}",
                    f"Description: {entity_data.get('description', '')}",
                    f"Status: {entity_data.get('status', '')}",
                    f"Mode: {entity_data.get('mode', '')}",
                ]
            )
            for attr in entity_data.get("attributes", []):
                text_parts.append(f"{attr.get('key', '')}: {attr.get('value', '')}")
        elif entity_type == "test_item":
            text_parts.extend(
                [
                    f"Test Item: {entity_data.get('name', '')}",
                    f"Description: {entity_data.get('description', '')}",
                    f"Type: {entity_data.get('type', '')}",
                    f"Status: {entity_data.get('status', '')}",
                ]
            )
            issue = entity_data.get("issue", {})
            if issue:
                text_parts.append(f"Issue Type: {issue.get('issueType', '')}")
                text_parts.append(f"Issue Comment: {issue.get('comment', '')}")
        elif entity_type == "log":
            text_parts.extend(
                [
                    f"Log Level: {entity_data.get('level', '')}",
                    f"Message: {entity_data.get('message', '')}",
                ]
            )
        elif entity_type == "user":
            text_parts.extend(
                [
                    f"User: {entity_data.get('userId', '')}",
                    f"Full Name: {entity_data.get('fullName', '')}",
                    f"Email: {entity_data.get('email', '')}",
                    f"Role: {entity_data.get('userRole', '')}",
                ]
            )
        elif entity_type == "project":
            text_parts.extend(
                [
                    f"Project: {entity_data.get('projectName', '')}",
                    f"Organization: {entity_data.get('organization', '')}",
                ]
            )

        return " ".join(filter(None, text_parts))

    async def upsert_documents(self, entity_type, entities, additional_metadata=None):
        if not entities:
            return 0

        try:
            documents = []
            ids = []
            metadatas = []

            for entity in entities:
                doc = self._prepare_document(entity_type, entity, additional_metadata)
                ids.append(doc["id"])
                documents.append(doc["document"])
                metadata = {
                    k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in doc["metadata"].items()
                }
                metadata["_entity_data"] = doc["entity_data"]
                metadatas.append(metadata)

            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

            logger.info("Upserted documents", entity_type=entity_type, count=len(entities))
            return len(entities)

        except Exception as e:
            logger.error("Failed to upsert documents", entity_type=entity_type, error=str(e))
            raise StorageError(f"Failed to upsert documents: {e}")

    async def get_existing_ids(self, entity_type):
        try:
            results = self._collection.get(
                where={"entity_type": entity_type},
                include=["metadatas"],
            )
            return set(results["ids"])

        except Exception as e:
            logger.error("Failed to get existing IDs", entity_type=entity_type, error=str(e))
            raise StorageError(f"Failed to get existing IDs: {e}")

    async def query(self, query_text, entity_types=None, n_results=10, where=None):
        try:
            conditions = []
            if entity_types:
                conditions.append({"entity_type": {"$in": entity_types}})
            if where:
                if "$and" in where:
                    conditions.extend(where["$and"])
                else:
                    for key, value in where.items():
                        conditions.append({key: value})
            if len(conditions) == 0:
                where_clause = None
            elif len(conditions) == 1:
                where_clause = conditions[0]
            else:
                where_clause = {"$and": conditions}

            results = self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause,
                include=["metadatas", "documents", "distances"],
            )

            processed_results = []
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                entity_data = json.loads(metadata.get("_entity_data", "{}"))

                processed_results.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": {k: v for k, v in metadata.items() if k != "_entity_data"},
                        "entity_data": entity_data,
                        "distance": results["distances"][0][i],
                    }
                )

            return processed_results

        except Exception as e:
            logger.error("Failed to query documents", error=str(e))
            raise StorageError(f"Failed to query documents: {e}")

    async def delete_by_entity_type(self, entity_type):
        try:
            existing_ids = await self.get_existing_ids(entity_type)
            if existing_ids:
                ids_list = list(existing_ids)
                batch_size = 5000
                for i in range(0, len(ids_list), batch_size):
                    batch = ids_list[i : i + batch_size]
                    self._collection.delete(ids=batch)
                logger.info("Deleted documents", entity_type=entity_type, count=len(existing_ids))
            return len(existing_ids)
        except Exception as e:
            logger.error("Failed to delete documents", entity_type=entity_type, error=str(e))
            raise StorageError(f"Failed to delete documents: {e}")

    async def get_statistics(self):
        try:
            entity_types = ["launch", "test_item", "log", "user", "project", "filter", "dashboard"]
            stats = {
                "total_documents": self._collection.count(),
                "by_entity_type": {},
            }
            for entity_type in entity_types:
                count = len(await self.get_existing_ids(entity_type))
                if count > 0:
                    stats["by_entity_type"][entity_type] = count
            return stats
        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            raise StorageError(f"Failed to get statistics: {e}")

"""ChromaDB client for vector storage."""

import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import structlog

from reportportal_ai.config.settings import settings
from reportportal_ai.core.exceptions import StorageError

logger = structlog.get_logger(__name__)


class ChromaDBClient:
    """Client for ChromaDB vector database operations."""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or str(settings.chroma_persist_directory)
        self.collection_name = collection_name or settings.chroma_collection_name
        
        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Initialize embedding function
        self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        
        # Get or create collection
        self._collection = self._get_or_create_collection()
        
    def _get_or_create_collection(self):
        """Get or create the ChromaDB collection."""
        try:
            return self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function,
                metadata={
                    "description": "ReportPortal data for AI assistant",
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error("Failed to create/get collection", error=str(e))
            raise StorageError(f"Failed to initialize collection: {e}")
    
    def _generate_id(self, entity_type: str, entity_data: Dict[str, Any]) -> str:
        """Generate a unique ID for an entity."""
        # Create a deterministic ID based on entity type and key fields
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
            # Fallback to hash-based ID
            content = json.dumps(entity_data, sort_keys=True)
            key = f"{entity_type}:{hashlib.md5(content.encode()).hexdigest()}"
        
        return key
    
    def _prepare_document(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare a document for storage."""
        # Extract text content for embedding
        text_content = self._extract_text_content(entity_type, entity_data)
        
        # Prepare metadata
        metadata = {
            "entity_type": entity_type,
            "entity_id": entity_data.get("id", ""),
            "created_at": datetime.utcnow().isoformat(),
            "last_modified": entity_data.get("lastModified", datetime.utcnow().isoformat()),
        }
        
        # Add entity-specific metadata
        if entity_type == "launch":
            metadata.update({
                "launch_name": entity_data.get("name", ""),
                "launch_number": entity_data.get("number", 0),
                "status": entity_data.get("status", ""),
                "mode": entity_data.get("mode", ""),
                "owner": entity_data.get("owner", ""),
            })
        elif entity_type == "test_item":
            metadata.update({
                "item_name": entity_data.get("name", ""),
                "item_type": entity_data.get("type", ""),
                "status": entity_data.get("status", ""),
                "launch_id": entity_data.get("launchId", ""),
            })
        elif entity_type == "log":
            metadata.update({
                "level": entity_data.get("level", ""),
                "item_id": entity_data.get("itemId", ""),
                "launch_id": entity_data.get("launchId", ""),
            })
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return {
            "id": self._generate_id(entity_type, entity_data),
            "document": text_content,
            "metadata": metadata,
            "entity_data": json.dumps(entity_data),  # Store full data as JSON
        }
    
    def _extract_text_content(self, entity_type: str, entity_data: Dict[str, Any]) -> str:
        """Extract text content from entity data for embedding."""
        text_parts = []
        
        if entity_type == "launch":
            text_parts.extend([
                f"Launch: {entity_data.get('name', '')}",
                f"Description: {entity_data.get('description', '')}",
                f"Status: {entity_data.get('status', '')}",
                f"Mode: {entity_data.get('mode', '')}",
            ])
            # Include attributes
            for attr in entity_data.get("attributes", []):
                text_parts.append(f"{attr.get('key', '')}: {attr.get('value', '')}")
                
        elif entity_type == "test_item":
            text_parts.extend([
                f"Test Item: {entity_data.get('name', '')}",
                f"Description: {entity_data.get('description', '')}",
                f"Type: {entity_data.get('type', '')}",
                f"Status: {entity_data.get('status', '')}",
            ])
            # Include issue information
            issue = entity_data.get("issue", {})
            if issue:
                text_parts.append(f"Issue Type: {issue.get('issueType', '')}")
                text_parts.append(f"Issue Comment: {issue.get('comment', '')}")
                
        elif entity_type == "log":
            text_parts.extend([
                f"Log Level: {entity_data.get('level', '')}",
                f"Message: {entity_data.get('message', '')}",
            ])
            
        elif entity_type == "user":
            text_parts.extend([
                f"User: {entity_data.get('userId', '')}",
                f"Full Name: {entity_data.get('fullName', '')}",
                f"Email: {entity_data.get('email', '')}",
                f"Role: {entity_data.get('userRole', '')}",
            ])
            
        elif entity_type == "project":
            text_parts.extend([
                f"Project: {entity_data.get('projectName', '')}",
                f"Organization: {entity_data.get('organization', '')}",
            ])
        
        return " ".join(filter(None, text_parts))
    
    async def upsert_documents(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Upsert multiple documents to ChromaDB."""
        if not entities:
            return 0
        
        try:
            # Prepare documents
            documents = []
            ids = []
            metadatas = []
            
            for entity in entities:
                doc = self._prepare_document(entity_type, entity, additional_metadata)
                ids.append(doc["id"])
                documents.append(doc["document"])
                
                # ChromaDB requires string values in metadata
                metadata = {
                    k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in doc["metadata"].items()
                }
                # Store entity data separately
                metadata["_entity_data"] = doc["entity_data"]
                metadatas.append(metadata)
            
            # Upsert to ChromaDB
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            
            logger.info(
                "Upserted documents",
                entity_type=entity_type,
                count=len(entities),
            )
            
            return len(entities)
            
        except Exception as e:
            logger.error(
                "Failed to upsert documents",
                entity_type=entity_type,
                error=str(e),
            )
            raise StorageError(f"Failed to upsert documents: {e}")
    
    async def get_existing_ids(self, entity_type: str) -> Set[str]:
        """Get existing document IDs for a given entity type."""
        try:
            # Query all documents of the given type
            results = self._collection.get(
                where={"entity_type": entity_type},
                include=["metadatas"],
            )
            
            return set(results["ids"])
            
        except Exception as e:
            logger.error(
                "Failed to get existing IDs",
                entity_type=entity_type,
                error=str(e),
            )
            raise StorageError(f"Failed to get existing IDs: {e}")
    
    async def query(
        self,
        query_text: str,
        entity_types: Optional[List[str]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query documents from ChromaDB."""
        try:
            # Build where clause
            where_clause = where or {}
            if entity_types:
                where_clause["entity_type"] = {"$in": entity_types}
            
            # Query ChromaDB
            results = self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"],
            )
            
            # Process results
            processed_results = []
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                entity_data = json.loads(metadata.get("_entity_data", "{}"))
                
                processed_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": {k: v for k, v in metadata.items() if k != "_entity_data"},
                    "entity_data": entity_data,
                    "distance": results["distances"][0][i],
                })
            
            return processed_results
            
        except Exception as e:
            logger.error("Failed to query documents", error=str(e))
            raise StorageError(f"Failed to query documents: {e}")
    
    async def delete_by_entity_type(self, entity_type: str) -> int:
        """Delete all documents of a given entity type."""
        try:
            # Get existing IDs
            existing_ids = await self.get_existing_ids(entity_type)
            
            if existing_ids:
                # Delete in batches
                ids_list = list(existing_ids)
                batch_size = 5000  # ChromaDB limit
                
                for i in range(0, len(ids_list), batch_size):
                    batch = ids_list[i:i + batch_size]
                    self._collection.delete(ids=batch)
                
                logger.info(
                    "Deleted documents",
                    entity_type=entity_type,
                    count=len(existing_ids),
                )
            
            return len(existing_ids)
            
        except Exception as e:
            logger.error(
                "Failed to delete documents",
                entity_type=entity_type,
                error=str(e),
            )
            raise StorageError(f"Failed to delete documents: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        try:
            # Get counts by entity type
            entity_types = [
                "launch", "test_item", "log", "user",
                "project", "filter", "dashboard"
            ]
            
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
"""Synchronization strategies for data sync."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


class SyncStrategy(ABC):
    """Base class for synchronization strategies."""
    
    @abstractmethod
    def filter_entities(
        self,
        entities: List[Dict[str, Any]],
        existing_ids: Set[str],
        id_generator: Callable[[Dict[str, Any]], str],
    ) -> List[Dict[str, Any]]:
        """
        Filter entities based on the strategy.
        
        Args:
            entities: List of entities to filter
            existing_ids: Set of existing entity IDs in storage
            id_generator: Function to generate ID from entity
            
        Returns:
            Filtered list of entities to sync
        """
        pass
    
    @abstractmethod
    def should_delete_missing(self) -> bool:
        """Whether to delete entities that are missing from the source."""
        pass


class FullSyncStrategy(SyncStrategy):
    """
    Full synchronization strategy.
    Syncs all entities regardless of their state.
    """
    
    def filter_entities(
        self,
        entities: List[Dict[str, Any]],
        existing_ids: Set[str],
        id_generator: Callable[[Dict[str, Any]], str],
    ) -> List[Dict[str, Any]]:
        """Return all entities for full sync."""
        return entities
    
    def should_delete_missing(self) -> bool:
        """Full sync should remove missing entities."""
        return True


class IncrementalSyncStrategy(SyncStrategy):
    """
    Incremental synchronization strategy.
    Only syncs new or modified entities.
    """
    
    def __init__(self, lookback_days: int = 7):
        """
        Initialize incremental sync strategy.
        
        Args:
            lookback_days: Number of days to look back for changes
        """
        self.lookback_days = lookback_days
        self.cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
    
    def filter_entities(
        self,
        entities: List[Dict[str, Any]],
        existing_ids: Set[str],
        id_generator: Callable[[Dict[str, Any]], str],
    ) -> List[Dict[str, Any]]:
        """Filter entities based on modification date or existence."""
        filtered = []
        
        for entity in entities:
            entity_id = id_generator(entity)
            
            # Include if new entity
            if entity_id not in existing_ids:
                filtered.append(entity)
                continue
            
            # Include if recently modified
            last_modified = entity.get("lastModified")
            if last_modified:
                try:
                    # Handle different date formats
                    if isinstance(last_modified, str):
                        if last_modified.isdigit():
                            # Unix timestamp in milliseconds
                            mod_date = datetime.fromtimestamp(int(last_modified) / 1000)
                        else:
                            # ISO format
                            mod_date = datetime.fromisoformat(
                                last_modified.replace("Z", "+00:00")
                            )
                    else:
                        # Assume it's already a datetime
                        mod_date = last_modified
                    
                    if mod_date > self.cutoff_date:
                        filtered.append(entity)
                except Exception as e:
                    logger.warning(
                        "Failed to parse modification date",
                        entity_id=entity_id,
                        last_modified=last_modified,
                        error=str(e),
                    )
                    # Include if we can't parse the date
                    filtered.append(entity)
        
        return filtered
    
    def should_delete_missing(self) -> bool:
        """Incremental sync should not delete missing entities."""
        return False


class SmartSyncStrategy(IncrementalSyncStrategy):
    """
    Smart synchronization strategy.
    Uses various heuristics to determine what needs to be synced.
    """
    
    def __init__(
        self,
        lookback_days: int = 7,
        priority_statuses: Optional[List[str]] = None,
        priority_issue_types: Optional[List[str]] = None,
    ):
        """
        Initialize smart sync strategy.
        
        Args:
            lookback_days: Number of days to look back for changes
            priority_statuses: List of statuses to prioritize (e.g., ["FAILED"])
            priority_issue_types: List of issue types to prioritize
        """
        super().__init__(lookback_days)
        self.priority_statuses = priority_statuses or ["FAILED", "BROKEN"]
        self.priority_issue_types = priority_issue_types or [
            "pb001",  # Product Bug
            "ab001",  # Automation Bug
            "si001",  # System Issue
        ]
    
    def filter_entities(
        self,
        entities: List[Dict[str, Any]],
        existing_ids: Set[str],
        id_generator: Callable[[Dict[str, Any]], str],
    ) -> List[Dict[str, Any]]:
        """Filter entities with smart heuristics."""
        # Start with incremental filter
        filtered = super().filter_entities(entities, existing_ids, id_generator)
        
        # Additionally include entities with priority status or issues
        priority_entities = []
        
        for entity in entities:
            entity_id = id_generator(entity)
            
            # Skip if already included
            if entity_id in {id_generator(e) for e in filtered}:
                continue
            
            # Check for priority status
            if entity.get("status") in self.priority_statuses:
                priority_entities.append(entity)
                continue
            
            # Check for priority issue types
            issue = entity.get("issue", {})
            if issue and issue.get("issueType") in self.priority_issue_types:
                priority_entities.append(entity)
                continue
            
            # For test items, check if they have recent failed children
            if entity.get("hasChildren") and entity.get("statistics"):
                stats = entity["statistics"]
                if stats.get("executions", {}).get("failed", 0) > 0:
                    priority_entities.append(entity)
        
        return filtered + priority_entities
    
    def should_delete_missing(self) -> bool:
        """Smart sync should not delete missing entities."""
        return False
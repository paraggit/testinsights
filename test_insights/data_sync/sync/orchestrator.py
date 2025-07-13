"""Orchestrator for data synchronization between ReportPortal and ChromaDB."""

import asyncio
from datetime import datetime, timedelta
from tqdm.asyncio import tqdm
import structlog

from test_insights.config.settings import settings
from test_insights.core.exceptions import SyncError
from test_insights.data_sync.api.client import ReportPortalAPIClient
from test_insights.data_sync.storage.chromadb_client import ChromaDBClient
from test_insights.data_sync.sync.strategies import SyncStrategy, FullSyncStrategy, IncrementalSyncStrategy

logger = structlog.get_logger(__name__)


class SyncOrchestrator:
    """Orchestrates data synchronization between ReportPortal and ChromaDB."""
    
    def __init__(
        self,
        api_client = None,
        storage_client = None,
    ):
        self.api_client = api_client
        self.storage_client = storage_client or ChromaDBClient()
        self._sync_metadata = {}
    
    async def sync(
        self,
        sync_type = "incremental",
        project_names = None,
        entity_types = None,
    ):
        """
        Perform data synchronization.
        
        Args:
            sync_type: Type of sync - "full" or "incremental"
            project_names: List of project names to sync. If None, sync all projects.
            entity_types: List of entity types to sync. If None, sync all types.
        
        Returns:
            Sync statistics
        """
        if sync_type not in ["full", "incremental"]:
            raise ValueError(f"Invalid sync type: {sync_type}")
        
        # Check feature flags
        if sync_type == "full" and not settings.enable_full_sync:
            raise SyncError("Full sync is disabled")
        if sync_type == "incremental" and not settings.enable_incremental_sync:
            raise SyncError("Incremental sync is disabled")
        
        # Default entity types
        if entity_types is None:
            entity_types = [
                "project", "user", "launch", "test_item",
                "log", "filter", "dashboard"
            ]
        
        logger.info(
            "Starting sync",
            sync_type=sync_type,
            entity_types=entity_types,
            project_names=project_names,
        )
        
        # Create API client if not provided
        if self.api_client is None:
            self.api_client = ReportPortalAPIClient()
        
        # Select sync strategy
        strategy: SyncStrategy
        if sync_type == "full":
            strategy = FullSyncStrategy(self.api_client, self.storage_client)
        else:
            strategy = IncrementalSyncStrategy()
        
        # Initialize stats
        start_time = datetime.utcnow()
        entity_stats = {}
        errors = []
        
        # Perform sync
        async with self.api_client:
            # Get projects to sync
            if project_names is None:
                projects = await self.api_client.get_projects()
                project_names = [p.get("projectName") for p in projects]
            
            # Sync each entity type
            for entity_type in entity_types:
                try:
                    if entity_type == "project":
                        count = await self.sync_projects()
                        entity_stats["project"] = count
                    
                    elif entity_type == "user":
                        count = await self.sync_users()
                        entity_stats["user"] = count
                    
                    elif entity_type == "launch":
                        total_count = 0
                        for project_name in project_names:
                            # For incremental sync, only get recent launches
                            filters = None
                            if isinstance(strategy, IncrementalSyncStrategy):
                                cutoff_timestamp = int(strategy.cutoff_date.timestamp() * 1000)
                                filters = {"filter.gte.startTime": cutoff_timestamp}
                            
                            count = await self.sync_launches(project_name, filters)
                            total_count += count
                        entity_stats["launch"] = total_count
                    
                    elif entity_type == "test_item":
                        # Test items are synced as part of launches
                        pass
                    
                    elif entity_type == "log":
                        # Logs are synced as part of test items
                        pass
                    
                    elif entity_type == "filter":
                        total_count = 0
                        for project_name in project_names:
                            count = await self.sync_filters(project_name)
                            total_count += count
                        entity_stats["filter"] = total_count
                    
                    elif entity_type == "dashboard":
                        total_count = 0
                        for project_name in project_names:
                            count = await self.sync_dashboards(project_name)
                            total_count += count
                        entity_stats["dashboard"] = total_count
                    
                except Exception as e:
                    logger.error(f"Failed to sync {entity_type}", error=str(e))
                    errors.append(f"{entity_type}: {str(e)}")
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Update sync metadata
        self._sync_metadata = {
            "last_sync": end_time.isoformat(),
            "sync_type": sync_type,
        }
        
        stats = {
            "entity_stats": entity_stats,
            "duration_seconds": duration,
            "errors": errors,
        }
        
        logger.info("Sync completed", stats=stats)
        return stats
    
    async def sync_projects(self):
        """Sync all projects."""
        logger.info("Syncing projects")
        
        projects = await self.api_client.get_projects()
        
        # Transform project data
        transformed_projects = []
        for project in projects:
            transformed_projects.append({
                "id": project.get("id"),
                "projectName": project.get("projectName"),
                "organization": project.get("organization"),
                "creationDate": project.get("creationDate"),
                "entryType": project.get("entryType"),
                "usersQuantity": project.get("usersQuantity", 0),
                "launchesQuantity": project.get("launchesQuantity", 0),
            })
        
        # Store in ChromaDB
        count = await self.storage_client.upsert_documents(
            "project",
            transformed_projects,
        )
        
        return count
    
    async def sync_users(self):
        """Sync all users."""
        logger.info("Syncing users")
        
        total_synced = 0
        page = 0
        
        with tqdm(desc="Syncing users") as pbar:
            while True:
                response = await self.api_client.get_users(
                    page=page,
                    size=settings.sync_batch_size,
                )
                
                if response.items:
                    count = await self.storage_client.upsert_documents(
                        "user",
                        response.items,
                    )
                    total_synced += count
                    pbar.update(count)
                
                if not response.has_next:
                    break
                
                page += 1
        
        return total_synced
    
    async def sync_launches(
        self,
        project_name,
        filters = None,
    ):
        """Sync launches for a project."""
        logger.info("Syncing launches", project=project_name)
        
        total_synced = 0
        page = 0
        
        with tqdm(desc=f"Syncing launches for {project_name}") as pbar:
            while True:
                response = await self.api_client.get_launches(
                    project_name,
                    page=page,
                    size=settings.sync_batch_size,
                    filters=filters,
                )
                
                if response.items:
                    # Add project context to metadata
                    count = await self.storage_client.upsert_documents(
                        "launch",
                        response.items,
                        additional_metadata={"project_name": project_name},
                    )
                    total_synced += count
                    pbar.update(count)
                    
                    # Sync test items for each launch
                    for launch in response.items:
                        await self.sync_test_items(
                            project_name,
                            launch["id"],
                        )
                
                if not response.has_next:
                    break
                
                page += 1
        
        return total_synced
    
    async def sync_test_items(
        self,
        project_name,
        launch_id,
    ):
        """Sync test items for a launch."""
        total_synced = 0
        page = 0
        
        while True:
            response = await self.api_client.get_test_items(
                project_name,
                launch_id,
                page=page,
                size=settings.sync_batch_size,
            )
            
            if response.items:
                # Add context to metadata
                count = await self.storage_client.upsert_documents(
                    "test_item",
                    response.items,
                    additional_metadata={
                        "project_name": project_name,
                        "launch_id": str(launch_id),
                    },
                )
                total_synced += count
                
                # Sync logs for failed items
                for item in response.items:
                    if item.get("status") in ["FAILED", "BROKEN"]:
                        await self.sync_logs(
                            project_name,
                            item["id"],
                        )
            
            if not response.has_next:
                break
            
            page += 1
        
        return total_synced
    
    async def sync_logs(
        self,
        project_name,
        item_id,
        max_logs = 100,
    ):
        """Sync logs for a test item (limited to avoid overwhelming storage)."""
        total_synced = 0
        page = 0
        
        while total_synced < max_logs:
            response = await self.api_client.get_logs(
                project_name,
                item_id,
                page=page,
                size=min(settings.sync_batch_size, max_logs - total_synced),
            )
            
            if response.items:
                # Filter only error/warn logs
                important_logs = [
                    log for log in response.items
                    if log.get("level") in ["error", "warn", "fatal"]
                ]
                
                if important_logs:
                    count = await self.storage_client.upsert_documents(
                        "log",
                        important_logs,
                        additional_metadata={
                            "project_name": project_name,
                            "item_id": str(item_id),
                        },
                    )
                    total_synced += count
            
            if not response.has_next or total_synced >= max_logs:
                break
            
            page += 1
        
        return total_synced
    
    async def sync_filters(self, project_name):
        """Sync filters for a project."""
        logger.info("Syncing filters", project=project_name)
        
        total_synced = 0
        page = 0
        
        while True:
            response = await self.api_client.get_filters(
                project_name,
                page=page,
                size=settings.sync_batch_size,
            )
            
            if response.items:
                count = await self.storage_client.upsert_documents(
                    "filter",
                    response.items,
                    additional_metadata={"project_name": project_name},
                )
                total_synced += count
            
            if not response.has_next:
                break
            
            page += 1
        
        return total_synced
    
    async def sync_dashboards(self, project_name):
        """Sync dashboards and their widgets for a project."""
        logger.info("Syncing dashboards", project=project_name)
        
        total_synced = 0
        page = 0
        
        while True:
            response = await self.api_client.get_dashboards(
                project_name,
                page=page,
                size=settings.sync_batch_size,
            )
            
            if response.items:
                # Enrich dashboard data with widget details
                enriched_dashboards = []
                for dashboard in response.items:
                    dashboard_data = dashboard.copy()
                    
                    # Get widget details
                    if "widgets" in dashboard_data:
                        widget_details = []
                        for widget in dashboard_data["widgets"]:
                            try:
                                widget_data = await self.api_client.get_widgets(
                                    project_name,
                                    widget["widgetId"],
                                )
                                widget_details.append(widget_data)
                            except Exception as e:
                                logger.warning(
                                    "Failed to get widget",
                                    widget_id=widget["widgetId"],
                                    error=str(e),
                                )
                        
                        dashboard_data["widget_details"] = widget_details
                    
                    enriched_dashboards.append(dashboard_data)
                
                count = await self.storage_client.upsert_documents(
                    "dashboard",
                    enriched_dashboards,
                    additional_metadata={"project_name": project_name},
                )
                total_synced += count
            
            if not response.has_next:
                break
            
            page += 1
        
        return total_synced
    
    async def get_sync_status(self):
        """Get current sync status and statistics."""
        stats = await self.storage_client.get_statistics()
        
        return {
            "storage_stats": stats,
            "last_sync": self._sync_metadata.get("last_sync"),
            "sync_type": self._sync_metadata.get("sync_type"),
        }
    
    async def cleanup_old_data(self, days = 90):
        """Clean up data older than specified days."""
        logger.info("Cleaning up old data", days=days)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # This is a placeholder - actual implementation would need to:
        # 1. Query documents with last_modified < cutoff_date
        # 2. Delete them in batches
        # 3. Return counts by entity type
        
        return {"message": "Cleanup not implemented yet"}
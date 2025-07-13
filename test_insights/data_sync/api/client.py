"""ReportPortal API client for data fetching."""

import asyncio
from typing import Any, Dict, List, Optional, TypeVar, Generic
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import structlog

from test_insights.config.settings import settings
from test_insights.core.exceptions import APIError, AuthenticationError, RateLimitError

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class PaginatedResponse(Generic[T]):
    """Represents a paginated response from the API."""
    
    def __init__(self, items: List[T], total: int, page: int, size: int):
        self.items = items
        self.total = total
        self.page = page
        self.size = size
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return (self.page + 1) * self.size < self.total


class ReportPortalAPIClient:
    """Async client for ReportPortal API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = base_url or settings.reportportal_base_url
        self.api_token = api_token or settings.reportportal_api_token
        self.timeout = timeout or settings.sync_timeout
        
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = asyncio.Semaphore(settings.sync_rate_limit)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            },
            timeout=self.timeout,
            verify=False,  # Disable SSL verification for testing purposes
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    @retry(
        stop=stop_after_attempt(settings.sync_max_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Execute an API request with rate limiting and retries."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        async with self._rate_limiter:
            try:
                response = await self._client.request(
                    method,
                    endpoint,
                    params=params,
                    json=json,
                )
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API token")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code >= 400:
                    raise APIError(
                        f"API error: {response.status_code} - {response.text}"
                    )
                
                return response
                
            except httpx.TimeoutException as e:
                logger.error("Request timeout", endpoint=endpoint, error=str(e))
                raise
            except httpx.NetworkError as e:
                logger.error("Network error", endpoint=endpoint, error=str(e))
                raise
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        response = await self._request("GET", "/v1/project/list")
        return response.json()
    
    async def get_launches(
        self,
        project_name: str,
        page: int = 0,
        size: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get launches for a project with pagination."""
        params = {
            "page.page": page,
            "page.size": size,
            "page.sort": "startTime,desc",
        }
        
        if filters:
            params.update(filters)
        
        response = await self._request(
            "GET",
            f"/v1/{project_name}/launch",
            params=params,
        )
        
        data = response.json()
        return PaginatedResponse(
            items=data.get("content", []),
            total=data.get("totalElements", 0),
            page=page,
            size=size,
        )
    
    async def get_test_items(
        self,
        project_name: str,
        launch_id: int,
        page: int = 0,
        size: int = 100,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get test items for a launch."""
        params = {
            "filter.eq.launchId": launch_id,
            "page.page": page,
            "page.size": size,
        }
        
        response = await self._request(
            "GET",
            f"/v1/{project_name}/item",
            params=params,
        )
        
        data = response.json()
        return PaginatedResponse(
            items=data.get("content", []),
            total=data.get("totalElements", 0),
            page=page,
            size=size,
        )
    
    async def get_logs(
        self,
        project_name: str,
        item_id: int,
        page: int = 0,
        size: int = 100,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get logs for a test item."""
        params = {
            "filter.eq.item": item_id,
            "page.page": page,
            "page.size": size,
        }
        
        response = await self._request(
            "GET",
            f"/v1/{project_name}/log",
            params=params,
        )
        
        data = response.json()
        return PaginatedResponse(
            items=data.get("content", []),
            total=data.get("totalElements", 0),
            page=page,
            size=size,
        )
    
    async def get_users(
        self,
        page: int = 0,
        size: int = 100,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get all users."""
        params = {
            "page.page": page,
            "page.size": size,
        }
        
        response = await self._request(
            "GET",
            "/users/all",
            params=params,
        )
        
        data = response.json()
        return PaginatedResponse(
            items=data.get("content", []),
            total=data.get("totalElements", 0),
            page=page,
            size=size,
        )
    
    async def get_filters(
        self,
        project_name: str,
        page: int = 0,
        size: int = 100,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get filters for a project."""
        params = {
            "page.page": page,
            "page.size": size,
        }
        
        response = await self._request(
            "GET",
            f"/v1/{project_name}/filter",
            params=params,
        )
        
        data = response.json()
        return PaginatedResponse(
            items=data.get("content", []),
            total=data.get("totalElements", 0),
            page=page,
            size=size,
        )
    
    async def get_dashboards(
        self,
        project_name: str,
        page: int = 0,
        size: int = 100,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """Get dashboards for a project."""
        params = {
            "page.page": page,
            "page.size": size,
        }
        
        response = await self._request(
            "GET",
            f"/v1/{project_name}/dashboard",
            params=params,
        )
        
        data = response.json()
        return PaginatedResponse(
            items=data.get("content", []),
            total=data.get("totalElements", 0),
            page=page,
            size=size,
        )
    
    async def get_widgets(
        self,
        project_name: str,
        widget_id: int,
    ) -> Dict[str, Any]:
        """Get a specific widget."""
        response = await self._request(
            "GET",
            f"/v1/{project_name}/widget/{widget_id}",
        )
        return response.json()
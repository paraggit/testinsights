"""ReportPortal API client for data fetching."""

import asyncio

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from test_insights.config.settings import settings
from test_insights.core.exceptions import APIError, AuthenticationError, RateLimitError

logger = structlog.get_logger(__name__)


class PaginatedResponse:
    """Represents a paginated response from the API."""

    def __init__(self, items, total, page, size):
        self.items = items
        self.total = total
        self.page = page
        self.size = size

    @property
    def has_next(self):
        """Check if there are more pages."""
        return (self.page + 1) * self.size < self.total


class ReportPortalAPIClient:
    """Async client for ReportPortal API."""

    def __init__(self, base_url=None, api_token=None, timeout=None):
        self.base_url = base_url or settings.reportportal_base_url
        self.api_token = api_token or settings.reportportal_api_token
        self.timeout = timeout or settings.sync_timeout

        self._client = None
        self._rate_limiter = asyncio.Semaphore(settings.sync_rate_limit)

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            },
            timeout=self.timeout,
            verify=False,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(settings.sync_max_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _request(self, method, endpoint, params=None, json=None):
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
                    raise APIError(f"API error: {response.status_code} - {response.text}")

                return response

            except httpx.TimeoutException as e:
                logger.error("Request timeout", endpoint=endpoint, error=str(e))
                raise
            except httpx.NetworkError as e:
                logger.error("Network error", endpoint=endpoint, error=str(e))
                raise

    async def get_projects(self):
        response = await self._request("GET", "/v1/project/list")
        return response.json()

    async def get_launches(self, project_name, page=0, size=100, filters=None):
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

    async def get_test_items(self, project_name, launch_id, page=0, size=100):
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

    async def get_logs(self, project_name, item_id, page=0, size=100):
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

    async def get_users(self, page=0, size=100):
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

    async def get_filters(self, project_name, page=0, size=100):
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

    async def get_dashboards(self, project_name, page=0, size=100):
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

    async def get_widgets(self, project_name, widget_id):
        response = await self._request(
            "GET",
            f"/v1/{project_name}/widget/{widget_id}",
        )
        return response.json()

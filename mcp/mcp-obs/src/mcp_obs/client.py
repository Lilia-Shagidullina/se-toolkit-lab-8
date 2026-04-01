"""HTTP client for VictoriaLogs and VictoriaTraces APIs."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


@dataclass
class ObsClient:
    """Client for querying VictoriaLogs and VictoriaTraces."""

    victorialogs_url: str
    victoriatraces_url: str
    _http: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> "ObsClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    # ─── VictoriaLogs methods ──────────────────────────────────────

    async def logs_search(
        self, query: str, limit: int = 100, time_range: str = "1h"
    ) -> list[dict]:
        """
        Search logs in VictoriaLogs using LogsQL.

        Args:
            query: LogsQL query string (e.g., 'severity:ERROR service.name:"backend"')
            limit: Maximum number of log entries to return
            time_range: Time range like '1h', '10m', '24h'

        Returns:
            List of log entries as dictionaries
        """
        client = await self._get_client()
        # Prepend time range if not already in query
        if not query.startswith("_time:"):
            query = f"_time:{time_range} {query}"

        url = f"{self.victorialogs_url}/select/logsql/query"
        response = await client.get(url, params={"query": query, "limit": limit})
        response.raise_for_status()
        return response.json()

    async def logs_error_count(
        self, service: str | None = None, time_range: str = "1h"
    ) -> dict:
        """
        Count errors per service over a time window.

        Args:
            service: Optional service name to filter by
            time_range: Time range like '1h', '10m', '24h'

        Returns:
            Dictionary with error counts
        """
        client = await self._get_client()
        query = f"_time:{time_range} severity:ERROR"
        if service:
            query += f' service.name:"{service}"'

        url = f"{self.victorialogs_url}/select/logsql/query"
        response = await client.get(url, params={"query": query, "limit": 1000})
        response.raise_for_status()
        data = response.json()

        # Count errors from the results
        if isinstance(data, list):
            return {"count": len(data), "time_range": time_range, "service": service}
        return {"count": 0, "time_range": time_range, "service": service}

    # ─── VictoriaTraces methods ──────────────────────────────────────

    async def traces_list(
        self, service: str | None = None, limit: int = 10
    ) -> list[dict]:
        """
        List recent traces for a service.

        Args:
            service: Service name to filter traces
            limit: Maximum number of traces to return

        Returns:
            List of trace summaries
        """
        client = await self._get_client()
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces"
        params: dict[str, str | int] = {"limit": limit}
        if service:
            params["service"] = service

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def traces_get(self, trace_id: str) -> dict:
        """
        Fetch a specific trace by ID.

        Args:
            trace_id: The trace ID to fetch

        Returns:
            Full trace data with spans
        """
        client = await self._get_client()
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces/{trace_id}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {})


async def main() -> None:
    """Test the client."""
    async with ObsClient(
        victorialogs_url="http://localhost:42010",
        victoriatraces_url="http://localhost:42011",
    ) as client:
        # Test logs search
        logs = await client.logs_search("severity:ERROR", limit=5)
        print(f"Found {len(logs)} error logs")

        # Test traces list
        traces = await client.traces_list(service="Learning Management Service", limit=3)
        print(f"Found {len(traces)} traces")


if __name__ == "__main__":
    asyncio.run(main())

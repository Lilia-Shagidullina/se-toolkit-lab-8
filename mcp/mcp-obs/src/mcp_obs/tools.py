"""Tool definitions for the observability MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from mcp.types import Tool
from pydantic import BaseModel

from mcp_obs.client import ObsClient


# ─── Tool argument models ──────────────────────────────────────


class LogsSearchParams(BaseModel):
    """Arguments for logs_search tool."""

    query: str = "severity:ERROR"
    limit: int = 50
    time_range: str = "1h"


class LogsErrorCountArgs(BaseModel):
    """Arguments for logs_error_count tool."""

    service: str | None = None
    time_range: str = "1h"


class TracesListArgs(BaseModel):
    """Arguments for traces_list tool."""

    service: str | None = None
    limit: int = 10


class TracesGetArgs(BaseModel):
    """Arguments for traces_get tool."""

    trace_id: str


# ─── Tool specs ──────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Tool specification."""

    name: str
    description: str
    model: type[BaseModel]
    handler: Callable[[ObsClient, BaseModel], Any]

    def as_tool(self) -> Tool:
        """Convert this spec to an MCP Tool."""
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def handle_logs_search(client: ObsClient, args: LogsSearchParams) -> dict:
    """Search logs using LogsQL."""
    result = await client.logs_search(
        query=args.query, limit=args.limit, time_range=args.time_range
    )
    return {"logs": result, "count": len(result) if isinstance(result, list) else 0}


async def handle_logs_error_count(
    client: ObsClient, args: LogsErrorCountArgs
) -> dict:
    """Count errors in a time window."""
    return await client.logs_error_count(
        service=args.service, time_range=args.time_range
    )


async def handle_traces_list(client: ObsClient, args: TracesListArgs) -> dict:
    """List recent traces."""
    traces = await client.traces_list(service=args.service, limit=args.limit)
    # Return summary info
    summaries = []
    for trace in traces:
        summary = {
            "trace_id": trace.get("traceID", trace.get("id", "unknown")),
            "span_count": len(trace.get("spans", [])),
            "services": list(
                {
                    span.get("processID", "unknown")
                    for span in trace.get("spans", [])
                }
            ),
        }
        summaries.append(summary)
    return {"traces": summaries, "count": len(summaries)}


async def handle_traces_get(client: ObsClient, args: TracesGetArgs) -> dict:
    """Get a specific trace by ID."""
    trace = await client.traces_get(trace_id=args.trace_id)
    if not trace:
        return {"error": f"Trace {args.trace_id} not found"}

    # Summarize the trace
    spans = trace.get("spans", [])
    span_summary = []
    for span in spans:
        span_info = {
            "operation": span.get("operationName", "unknown"),
            "duration_ms": span.get("duration", 0) / 1000,  # Convert to ms
            "has_error": any(
                tag.get("key") == "error" and tag.get("value") == "true"
                for tag in span.get("tags", [])
            ),
        }
        span_summary.append(span_info)

    return {
        "trace_id": args.trace_id,
        "span_count": len(spans),
        "spans": span_summary,
        "has_error": any(s["has_error"] for s in span_summary),
    }


# ─── Tool registry ──────────────────────────────────────

TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="mcp_obs_logs_search",
        description="Search logs in VictoriaLogs using LogsQL. Use this to find log entries matching specific criteria like severity level, service name, or keywords. Returns matching log entries.",
        model=LogsSearchParams,
        handler=handle_logs_search,
    ),
    ToolSpec(
        name="mcp_obs_logs_error_count",
        description="Count error logs per service over a time window. Use this first to check if there are any errors before diving into detailed log search.",
        model=LogsErrorCountArgs,
        handler=handle_logs_error_count,
    ),
    ToolSpec(
        name="mcp_obs_traces_list",
        description="List recent traces for a service. Use this to see what request traces are available for analysis.",
        model=TracesListArgs,
        handler=handle_traces_list,
    ),
    ToolSpec(
        name="mcp_obs_traces_get",
        description="Fetch a specific trace by ID. Use this to inspect the full span hierarchy of a request, including errors and timing information.",
        model=TracesGetArgs,
        handler=handle_traces_get,
    ),
]

TOOLS_BY_NAME: dict[str, ToolSpec] = {spec.name: spec for spec in TOOL_SPECS}

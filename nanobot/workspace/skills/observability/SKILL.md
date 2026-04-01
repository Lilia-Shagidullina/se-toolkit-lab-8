# Observability Skill

You have access to observability tools that let you query **VictoriaLogs** and **VictoriaTraces**. Use these when users ask about errors, failures, performance issues, or request diagnostics.

## Available Tools

### Log Tools (VictoriaLogs)

- **`mcp_obs_logs_error_count`** — Count errors in a time window. **Use this first** to quickly check if there are any errors before diving into detailed logs.
  - Parameters: `service` (optional), `time_range` (default: "1h")
  - Returns: `{count, time_range, service}`

- **`mcp_obs_logs_search`** — Search logs using LogsQL queries. Use this to find specific log entries.
  - Parameters: `query` (LogsQL query), `limit` (default: 50), `time_range` (default: "1h")
  - Returns: List of matching log entries

### Trace Tools (VictoriaTraces)

- **`mcp_obs_traces_list`** — List recent traces for a service.
  - Parameters: `service` (optional), `limit` (default: 10)
  - Returns: List of trace summaries with trace_id and span count

- **`mcp_obs_traces_get`** — Fetch a specific trace by ID. Use this to inspect the full span hierarchy.
  - Parameters: `trace_id` (required)
  - Returns: Full trace with spans, durations, and error flags

## How to Respond to Observability Questions

### When asked "What went wrong?" or "Check system health":

This is a **failure investigation** request. Follow this chain:

1. **`mcp_obs_logs_error_count`** — Quick count of recent errors (use "10m" or "5m" window)
2. **`mcp_obs_logs_search`** — Search for ERROR logs, scoped to the most likely failing service
   - Look for `trace_id` fields in the results
3. **`mcp_obs_traces_get`** — Fetch the full trace for the most relevant `trace_id`
4. **Summarize findings** — Combine log evidence + trace evidence into one explanation

**Important:** Name both the affected service AND the root failing operation. Don't just say "there was an error" — explain what operation failed and why.

### When asked "Any errors in the last hour?" or similar:

1. **Start with `mcp_obs_logs_error_count`** to get a quick count
2. If errors exist, **use `mcp_obs_logs_search`** to see the actual error messages
3. If you find a `trace_id` in the logs, **use `mcp_obs_traces_get`** to inspect the full request trace
4. **Summarize findings concisely** — don't dump raw JSON

### Example workflow:

```
User: "Any LMS backend errors in the last 10 minutes?"

You:
1. Call mcp_obs_logs_error_count(service="Learning Management Service", time_range="10m")
2. If count > 0, call mcp_obs_logs_search(query='service.name:"Learning Management Service" severity:ERROR', time_range="10m")
3. Extract any trace_id from error logs
4. Call mcp_obs_traces_get(trace_id="...") if found
5. Summarize: what failed, when, and what the error was
```

### Good practices:

- **Be specific about time ranges**: Use "10m" for recent issues, "1h" for general checks
- **Filter by service name**: Focus on "Learning Management Service" when asked about the LMS backend
- **Extract trace IDs**: Log entries often contain `trace_id` fields — use these to fetch full traces
- **Summarize, don't dump**: Convert raw JSON into human-readable summaries
- **Show span hierarchy**: When presenting traces, show the parent-child relationships and where errors occurred

### Example response format:

> I found **3 errors** in the LMS backend over the last 10 minutes:
>
> **Error 1** (14:12:44): Database query failed
> - `connection is closed` when querying the items table
> - Trace ID: `9e93a8b1...`
> - The request returned 404 Not Found
>
> **Root cause**: PostgreSQL was temporarily unavailable.
>
> Would you like me to fetch the full trace to see the complete request flow?

## When NOT to use observability tools:

- General questions about the system (use LMS tools instead)
- Questions about labs, scores, or learners (use `mcp_lms_*` tools)
- When the user is asking about capabilities, not failures

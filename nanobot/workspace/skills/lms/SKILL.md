---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to LMS MCP tools that provide live data from the Learning Management System backend. Use these tools strategically to answer user questions about labs, learners, and course analytics.

## Available Tools

- `lms_health` — Check if the LMS backend is healthy and get the item count
- `lms_labs` — List all labs available in the LMS
- `lms_learners` — List all learners registered in the LMS
- `lms_pass_rates` — Get pass rates (avg score and attempt count per task) for a lab
- `lms_timeline` — Get submission timeline (date + submission count) for a lab
- `lms_groups` — Get group performance (avg score + student count per group) for a lab
- `lms_top_learners` — Get top learners by average score for a lab
- `lms_completion_rate` — Get completion rate (passed / total) for a lab
- `lms_sync_pipeline` — Trigger the LMS sync pipeline (may take a moment)

## Strategy

### When the user asks about scores, pass rates, completion, groups, timeline, or top learners without naming a lab:

1. Call `lms_labs` first to get the list of available labs
2. Use `mcp_webchat_ui_message` with `type: "choice"` to ask the user which lab they want
3. Use each lab's `title` field as the choice label and the `lab` field as the value
4. Once the user selects a lab, call the appropriate tool with the selected lab identifier

### When the user asks "what can you do?":

Explain your current tools and limits clearly:
- You can query live LMS data about labs, learners, pass rates, completion rates, timelines, and group performance
- You need a lab identifier for most analytics queries
- You can trigger the sync pipeline to refresh data from the autochecker

### Formatting responses:

- Format numeric results nicely: show percentages as "X%" and counts as plain numbers
- Keep responses concise — lead with the answer, then offer to dive deeper
- When presenting multiple items (labs, learners, groups), use bullet points or numbered lists

### Lab selection:

- When multiple labs are available and the user hasn't specified one, always ask for clarification
- Use the lab's full title (e.g., "Lab 01 — Products, Architecture & Roles") as the user-facing label
- Pass the lab identifier (e.g., "lab-01") to the tool calls

### Error handling:

- If a tool call fails, explain what went wrong in simple terms
- If the backend is unhealthy or returns no data, suggest running `lms_sync_pipeline`
- If the user provides an invalid lab identifier, call `lms_labs` and show available options

# Nanobot gateway Dockerfile
# Follows the same uv multi-stage pattern as backend/Dockerfile

ARG REGISTRY_PREFIX_DOCKER_HUB

# ---
# Stage 1: Build the application
# ---

FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files for dependency resolution
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy nanobot and MCP package definitions
COPY --from=workspace nanobot/pyproject.toml /app/nanobot/pyproject.toml
COPY --from=workspace mcp/mcp-lms/pyproject.toml /app/mcp/mcp-lms/pyproject.toml
COPY --from=workspace mcp/mcp-obs/pyproject.toml /app/mcp/mcp-obs/pyproject.toml
COPY --from=workspace nanobot-websocket-channel/nanobot-channel-protocol/pyproject.toml /app/nanobot-websocket-channel/nanobot-channel-protocol/pyproject.toml
COPY --from=workspace nanobot-websocket-channel/mcp-webchat/pyproject.toml /app/nanobot-websocket-channel/mcp-webchat/pyproject.toml
COPY --from=workspace nanobot-websocket-channel/nanobot-webchat/pyproject.toml /app/nanobot-websocket-channel/nanobot-webchat/pyproject.toml

# Sync nanobot dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package nanobot

# Copy the rest of nanobot source
COPY --from=workspace nanobot/ /app/nanobot/
COPY --from=workspace mcp/mcp-lms/ /app/mcp/mcp-lms/
COPY --from=workspace mcp/mcp-obs/ /app/mcp/mcp-obs/
COPY --from=workspace nanobot-websocket-channel/nanobot-channel-protocol/ /app/nanobot-websocket-channel/nanobot-channel-protocol/
COPY --from=workspace nanobot-websocket-channel/mcp-webchat/ /app/nanobot-websocket-channel/mcp-webchat/
COPY --from=workspace nanobot-websocket-channel/nanobot-webchat/ /app/nanobot-websocket-channel/nanobot-webchat/

# Sync again to install the local nanobot package and its workspace dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot

# ---
# Stage 2: Runtime image
# ---

FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Create non-root user matching host UID/GID for bind mounts
RUN groupadd --system --gid 1000 appgroup \
    && useradd --system --gid 1000 --uid 1000 --create-home appuser

# Copy application from builder
COPY --from=builder --chown=appuser:appgroup /app /app

# Put venv in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Use non-root user
USER appuser

WORKDIR /app

# Run the entrypoint which resolves config and starts gateway
CMD ["python", "/app/nanobot/entrypoint.py"]

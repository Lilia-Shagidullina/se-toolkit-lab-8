#!/usr/bin/env python3
"""Resolve environment variables into nanobot config, then launch the gateway."""

import json
import os
import tempfile
from pathlib import Path


def main():
    config_path = Path(__file__).parent / "config.json"
    workspace = os.environ.get("NANOBOT_WORKSPACE", "./workspace")
    # Write resolved config to /tmp to avoid permission issues with bind-mounted volumes
    resolved_path = Path(tempfile.gettempdir()) / "nanobot-config.resolved.json"

    # Read base config
    with open(config_path) as f:
        config = json.load(f)

    # Override LLM provider settings from env vars
    if "LLM_API_KEY" in os.environ:
        config["providers"]["custom"]["apiKey"] = os.environ["LLM_API_KEY"]
    if "LLM_API_BASE_URL" in os.environ:
        config["providers"]["custom"]["apiBase"] = os.environ["LLM_API_BASE_URL"]
    if "LLM_API_MODEL" in os.environ:
        config["agents"]["defaults"]["model"] = os.environ["LLM_API_MODEL"]

    # Override gateway settings
    if "NANOBOT_GATEWAY_CONTAINER_ADDRESS" in os.environ:
        config["gateway"]["host"] = os.environ["NANOBOT_GATEWAY_CONTAINER_ADDRESS"]
    if "NANOBOT_GATEWAY_CONTAINER_PORT" in os.environ:
        config["gateway"]["port"] = int(os.environ["NANOBOT_GATEWAY_CONTAINER_PORT"])

    # Configure webchat channel from env vars
    if "NANOBOT_WEBCHAT_CONTAINER_ADDRESS" in os.environ:
        if "webchat" not in config["channels"]:
            config["channels"]["webchat"] = {}
        config["channels"]["webchat"]["enabled"] = True
        config["channels"]["webchat"]["host"] = os.environ["NANOBOT_WEBCHAT_CONTAINER_ADDRESS"]
    if "NANOBOT_WEBCHAT_CONTAINER_PORT" in os.environ:
        if "webchat" not in config["channels"]:
            config["channels"]["webchat"] = {"enabled": True}
        config["channels"]["webchat"]["port"] = int(os.environ["NANOBOT_WEBCHAT_CONTAINER_PORT"])
        config["channels"]["webchat"]["enabled"] = True

    # Configure MCP servers from env vars
    if "mcpServers" not in config["tools"]:
        config["tools"]["mcpServers"] = {}

    # LMS MCP server
    if "NANOBOT_LMS_BACKEND_URL" in os.environ or "NANOBOT_LMS_API_KEY" in os.environ:
        if "lms" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["lms"] = {
                "command": "python",
                "args": ["-m", "mcp_lms"],
                "env": {}
            }
        if "env" not in config["tools"]["mcpServers"]["lms"]:
            config["tools"]["mcpServers"]["lms"]["env"] = {}
        if "NANOBOT_LMS_BACKEND_URL" in os.environ:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = os.environ["NANOBOT_LMS_BACKEND_URL"]
        if "NANOBOT_LMS_API_KEY" in os.environ:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = os.environ["NANOBOT_LMS_API_KEY"]

    # Webchat MCP server (for structured UI messages)
    if "NANOBOT_WEBCHAT_UI_RELAY_URL" in os.environ or "NANOBOT_WEBCHAT_UI_TOKEN" in os.environ:
        if "webchat" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["webchat"] = {
                "command": "python",
                "args": ["-m", "mcp_webchat"],
                "env": {}
            }
        if "env" not in config["tools"]["mcpServers"]["webchat"]:
            config["tools"]["mcpServers"]["webchat"]["env"] = {}
        if "NANOBOT_WEBCHAT_UI_RELAY_URL" in os.environ:
            config["tools"]["mcpServers"]["webchat"]["env"]["NANOBOT_WEBCHAT_UI_RELAY_URL"] = os.environ["NANOBOT_WEBCHAT_UI_RELAY_URL"]
        if "NANOBOT_WEBCHAT_UI_TOKEN" in os.environ:
            config["tools"]["mcpServers"]["webchat"]["env"]["NANOBOT_WEBCHAT_UI_TOKEN"] = os.environ["NANOBOT_WEBCHAT_UI_TOKEN"]

    # Observability MCP server (VictoriaLogs and VictoriaTraces)
    if "NANOBOT_VICTORIALOGS_URL" in os.environ or "NANOBOT_VICTORIATRACES_URL" in os.environ:
        if "obs" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["obs"] = {
                "command": "python",
                "args": ["-m", "mcp_obs"],
                "env": {}
            }
        if "env" not in config["tools"]["mcpServers"]["obs"]:
            config["tools"]["mcpServers"]["obs"]["env"] = {}
        if "NANOBOT_VICTORIALOGS_URL" in os.environ:
            config["tools"]["mcpServers"]["obs"]["env"]["NANOBOT_VICTORIALOGS_URL"] = os.environ["NANOBOT_VICTORIALOGS_URL"]
        if "NANOBOT_VICTORIATRACES_URL" in os.environ:
            config["tools"]["mcpServers"]["obs"]["env"]["NANOBOT_VICTORIATRACES_URL"] = os.environ["NANOBOT_VICTORIATRACES_URL"]

    # Webchat channel configuration from env vars
    # Access key validation happens at WebSocket connection time, not at sender level
    # So allowFrom should be ["*"] to allow all authenticated senders
    if "NANOBOT_WEBCHAT_CONTAINER_ADDRESS" in os.environ or "NANOBOT_WEBCHAT_CONTAINER_PORT" in os.environ:
        if "webchat" not in config["channels"]:
            config["channels"]["webchat"] = {"enabled": True}
        else:
            config["channels"]["webchat"]["enabled"] = True
        if "NANOBOT_WEBCHAT_CONTAINER_ADDRESS" in os.environ:
            config["channels"]["webchat"]["host"] = os.environ["NANOBOT_WEBCHAT_CONTAINER_ADDRESS"]
        if "NANOBOT_WEBCHAT_CONTAINER_PORT" in os.environ:
            config["channels"]["webchat"]["port"] = int(os.environ["NANOBOT_WEBCHAT_CONTAINER_PORT"])
        # Allow all authenticated senders (access key is validated at WebSocket connection)
        config["channels"]["webchat"]["allowFrom"] = ["*"]

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using resolved config: {resolved_path}")

    # Launch nanobot gateway
    os.execvp("nanobot", ["nanobot", "gateway", "--config", str(resolved_path), "--workspace", workspace])


if __name__ == "__main__":
    main()

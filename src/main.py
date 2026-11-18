"""Starts the orchestrator service: config -> tools -> graph -> HTTP server."""
import uvicorn

from .checkpointing import get_checkpointer
from .config import load_settings
from .graph import build_graph
from .tools import build_tools
from .webhook import create_app


def main():
    settings = load_settings()
    tools = build_tools(settings)
    with get_checkpointer(settings.secret("postgres_dsn_env") or None) as checkpointer:
        graph = build_graph(tools, settings, checkpointer)
        app = create_app(graph, tools, settings.secret("webhook_secret_env"))
        uvicorn.run(app, host="0.0.0.0", port=8080)  # single ingress for signed webhooks


if __name__ == "__main__":
    main()

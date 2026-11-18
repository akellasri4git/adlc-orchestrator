"""Starts the orchestrator service: config -> tools -> graph -> HTTP server."""
import os
import uvicorn

from .checkpointing import get_checkpointer
from .config import load_settings
from .graph import build_graph
from .tools import build_tools
from .webhook import create_app


def main():
    settings = load_settings()
    tools = build_tools(settings)
    mock_mode = os.getenv("ADLC_MODE", "real").strip().lower() == "mock"
    dsn = None if mock_mode else settings.secret("postgres_dsn_env")
    webhook_secret = os.getenv("ADLC_WEBHOOK_SECRET", "demo-secret") if mock_mode else settings.secret("webhook_secret_env")
    host = os.getenv("ADLC_HOST", "127.0.0.1" if mock_mode else "0.0.0.0")
    port = int(os.getenv("ADLC_PORT", "8080"))
    with get_checkpointer(dsn or None) as checkpointer:
        graph = build_graph(tools, settings, checkpointer)
        app = create_app(graph, tools, webhook_secret)
        uvicorn.run(app, host=host, port=port)  # single ingress for signed webhooks


if __name__ == "__main__":
    main()

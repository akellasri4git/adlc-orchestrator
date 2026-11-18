"""HTTP entry points: start a run, and receive signed Jira approval webhooks.
Expected webhook body (configure in a Jira Automation rule):
  {"change_id": "CHANGE-123", "stage": "design", "decision": "approved" | "changes_requested", "comments": "..."}"""
import hashlib
import hmac
import json

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from langgraph.types import Command

from .state import new_run_state


def create_app(graph, tools, webhook_secret: str) -> FastAPI:
    app = FastAPI(title="ADLC Orchestrator")

    def cfg(change_id):
        return {"configurable": {"thread_id": change_id}}

    @app.post("/runs")
    def start_run(payload: dict, background: BackgroundTasks):
        cid = payload["change_id"]
        if graph.get_state(cfg(cid)).values:
            raise HTTPException(409, "run already exists for this change")
        if not tools.jira.is_ready(cid):
            raise HTTPException(422, "change request is not labelled for ADLC / not Ready for ADLC")
        background.add_task(graph.invoke, new_run_state(cid), cfg(cid))
        return {"accepted": True, "change_id": cid}

    @app.post("/webhooks/jira")
    async def jira_webhook(request: Request, background: BackgroundTasks,
                           x_hub_signature_256: str = Header(default="")):
        body = await request.body()
        expected = "sha256=" + hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        if not webhook_secret or not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(401, "bad signature")

        event = json.loads(body)
        cid, stage = event["change_id"], event["stage"]
        if f"gate_{stage}" not in graph.get_state(cfg(cid)).next:
            raise HTTPException(409, f"run is not waiting at the {stage} gate")

        resume = {"decision": event["decision"], "comments": event.get("comments", "")}
        background.add_task(graph.invoke, Command(resume=resume), cfg(cid))
        return {"accepted": True}

    return app

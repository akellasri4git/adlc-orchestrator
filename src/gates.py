"""Approval gates. Each stage is followed by two nodes:
  request_<stage>: posts the approval request to Jira (runs once)
  gate_<stage>:    pauses the run with a LangGraph interrupt

They are separate because LangGraph re-runs a node from its start on resume.
Anything before interrupt() would repeat, and we must not post to Jira twice."""
from langgraph.types import interrupt

from .state import NEXT


def make_request_node(stage, tools, settings):
    def node(state):
        if not settings.gate_enabled(stage):
            return {}
        summary = f"Outputs: {list(state['outputs'].get(stage, {}))}. Evidence: {state['evidence_ids'][-1:]}"
        tools.jira.request_approval(state["change_id"], stage, summary)
        return {"status": "waiting_gate"}
    return node


def make_gate_node(stage, settings):
    def node(state):
        decisions = dict(state.get("gate_decisions", {}))
        if not settings.gate_enabled(stage):  # only possible via an approved config change
            decisions[stage] = "approved"
            return {"gate_decisions": decisions, "status": "running"}
        # Pauses here. Resumed with Command(resume={"decision": ..., "comments": ...}).
        reply = interrupt({"change_id": state["change_id"], "stage": stage, "awaiting": "approval"})
        decision = reply.get("decision", "changes_requested")
        decisions[stage] = decision if decision in ("approved", "changes_requested") else "changes_requested"
        done = decisions[stage] == "approved" and stage not in NEXT
        return {
            "gate_decisions": decisions, "status": "completed" if done else "running",
            "feedback": reply.get("comments", "") if decisions[stage] == "changes_requested" else "",
        }
    return node


def route_after_gate(stage):
    """approved -> next stage (or finish); changes requested -> re-run the same stage."""
    def route(state):
        if state["gate_decisions"].get(stage) == "approved":
            return "next" if stage in NEXT else "done"
        return "same"
    return route

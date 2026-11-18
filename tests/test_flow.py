"""End-to-end tests with stub tools and in-memory checkpointing."""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.config import load_settings
from src.graph import build_graph
from src.state import new_run_state
from src.tools import stub_tools
from src.tools.copilot_cli_tool import StubCopilotCliTool

APPROVE = Command(resume={"decision": "approved", "comments": ""})


def make(script=None):
    copilot = StubCopilotCliTool(script)
    tools = stub_tools(copilot=copilot)
    graph = build_graph(tools, load_settings(), MemorySaver())
    return graph, tools, copilot, {"configurable": {"thread_id": "CHANGE-1"}}


def test_happy_path_pauses_at_every_gate_then_completes():
    graph, tools, copilot, cfg = make()
    graph.invoke(new_run_state("CHANGE-1"), cfg)
    for stage in ["requirements", "design", "developer", "testing", "security"]:
        assert graph.get_state(cfg).next == (f"gate_{stage}",)
        graph.invoke(APPROVE, cfg)
    assert graph.get_state(cfg).next == ()
    assert graph.get_state(cfg).values["status"] == "completed"
    assert copilot.calls == ["requirements", "design", "developer", "testing", "security"]
    assert len(tools.jira.approvals) == 5


def test_changes_requested_reruns_same_stage():
    graph, _, copilot, cfg = make()
    graph.invoke(new_run_state("CHANGE-1"), cfg)
    graph.invoke(Command(resume={"decision": "changes_requested", "comments": "fix AC-2"}), cfg)
    assert copilot.calls == ["requirements", "requirements"]
    assert graph.get_state(cfg).next == ("gate_requirements",)


def test_testing_failure_routes_back_to_developer():
    graph, _, copilot, cfg = make({"testing": ["fail", "pass"]})
    graph.invoke(new_run_state("CHANGE-1"), cfg)
    for _ in range(3):           # requirements, design, developer gates
        graph.invoke(APPROVE, cfg)
    assert copilot.calls[-2:] == ["testing", "developer"]
    # testing failed, so the run went back to developer and is waiting at the code gate
    assert graph.get_state(cfg).next == ("gate_developer",)
    assert graph.get_state(cfg).values["loop_counts"]["testing"] == 1


def test_repair_cap_halts_the_run():
    graph, tools, _, cfg = make({"testing": ["fail"] * 10})
    graph.invoke(new_run_state("CHANGE-1"), cfg)
    for _ in range(3):
        graph.invoke(APPROVE, cfg)
    while graph.get_state(cfg).next:
        graph.invoke(APPROVE, cfg)
    vals = graph.get_state(cfg).values
    assert vals["status"] == "halted" and vals["halt_reason"] == "repair-loop cap reached"
    assert any("repair loops" in c[1] for c in tools.jira.comments)

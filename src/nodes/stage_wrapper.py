"""One reusable wrapper for every stage:
entry checks -> context pack -> policy -> budget -> agent call -> output screen -> exit checks -> evidence."""
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..state import PREVIOUS


@dataclass(frozen=True)
class StageSpec:
    name: str
    agent: str                 # native Copilot agent
    skill: str                 # skill the agent loads
    expected_outputs: list     # files that must exist at exit
    requires_pass_verdict: bool = False   # testing / security
    repairable: bool = False              # failures route back to Developer
    pre_hook: Optional[Callable] = None   # e.g. create the change branch
    post_hook: Optional[Callable] = None  # e.g. open the pull request


def _halt(state, stage, reason, tools):
    tools.jira.comment(state["change_id"], f"[ADLC] Run halted at {stage}: {reason}")
    return {"stage": stage, "status": "halted", "halt_reason": reason}


def make_stage_node(spec: StageSpec, tools, settings):
    def node(state):
        cid, stage = state["change_id"], spec.name

        # Entry criteria
        prev = PREVIOUS.get(stage)
        if prev and state.get("gate_decisions", {}).get(prev) != "approved":
            return _halt(state, stage, f"entry: {prev} gate not approved", tools)
        if not tools.budget.check(cid, stage, settings.credit_headroom[stage])["allowed"]:
            return _halt(state, stage, "entry: insufficient credit headroom", tools)
        if spec.pre_hook:
            spec.pre_hook(state, tools)

        pack = tools.context.build(cid, stage, spec.skill, state.get("outputs", {}), state.get("feedback", ""))
        if tools.policy.screen_input(pack)["verdict"] == "block":
            return _halt(state, stage, "context pack blocked by guardrails", tools)
        perms = tools.policy.issue_permissions(cid, stage)
        if perms["verdict"] == "block":
            return _halt(state, stage, "policy blocked this stage", tools)

        # Agent call
        result = tools.copilot.run(stage=stage, agent=spec.agent, skill=spec.skill,
                                   context_pack=pack["path"], permissions=perms,
                                   feedback=state.get("feedback", ""))
        if tools.policy.screen_output(result)["verdict"] == "block":
            return _halt(state, stage, "agent output blocked by guardrails", tools)
        tools.budget.record(cid, stage, result.get("credits_used", 0))

        # Exit criteria
        missing = [f for f in spec.expected_outputs if f not in result.get("outputs", {})]
        passed = result.get("ok", False) and not missing
        if spec.requires_pass_verdict:
            passed = passed and result.get("verdict") == "pass"
        passed = passed and tools.evidence.check_completeness(cid, stage)["complete"]
        eid = tools.evidence.record(cid, stage, {"passed": passed, "missing": missing,
                                                  "pack_hash": pack["hash"]})
        if passed and spec.post_hook:
            spec.post_hook(state, tools)

        update = {
            "stage": stage, "status": "running",
            "outputs": {**state.get("outputs", {}), stage: result.get("outputs", {})},
            "last_result": {"passed": passed, "missing": missing, "findings": result.get("findings", "")},
            "credit_ledger": [{"stage": stage, "credits": result.get("credits_used", 0)}],
            "evidence_ids": [eid],
        }
        if passed:
            update["feedback"] = ""
        elif spec.repairable:
            loops = dict(state.get("loop_counts", {}))
            loops[stage] = loops.get(stage, 0) + 1
            update["loop_counts"] = loops
            update["feedback"] = result.get("findings", "")
            if loops[stage] > settings.repair_loop_cap:
                tools.jira.comment(cid, f"[ADLC] {stage} still failing after {settings.repair_loop_cap} repair loops.")
                update.update(status="halted", halt_reason="repair-loop cap reached")
        else:
            tools.jira.comment(cid, f"[ADLC] {stage} exit criteria not met: {missing}")
            update.update(status="halted", halt_reason=f"exit criteria not met: {missing}")
        return update

    return node

"""The single run state LangGraph passes between nodes (section 5.1)."""
import operator
from typing import Annotated, TypedDict

STAGES = ["requirements", "design", "developer", "testing", "security"]
PREVIOUS = {s: STAGES[i - 1] for i, s in enumerate(STAGES) if i > 0}
NEXT = {s: STAGES[i + 1] for i, s in enumerate(STAGES[:-1])}


class RunState(TypedDict, total=False):
    change_id: str                 # Jira key, also the LangGraph thread_id
    stage: str                     # stage currently running / last run
    status: str                    # running | waiting_gate | completed | halted
    gate_decisions: dict           # {stage: approved | changes_requested}
    outputs: dict                  # {stage: {filename: path}}
    loop_counts: dict              # {testing: n, security: n} repair-loop counts
    feedback: str                  # reviewer comments or failure findings for the next run
    last_result: dict              # result of the most recent stage run
    halt_reason: str
    credit_ledger: Annotated[list, operator.add]   # appended to, never overwritten
    evidence_ids: Annotated[list, operator.add]


def new_run_state(change_id: str) -> RunState:
    return {
        "change_id": change_id, "stage": "requirements", "status": "running",
        "gate_decisions": {}, "outputs": {}, "loop_counts": {}, "feedback": "",
        "last_result": {}, "halt_reason": "", "credit_ledger": [], "evidence_ids": [],
    }

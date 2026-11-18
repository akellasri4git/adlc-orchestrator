"""Conditional routing after a stage runs."""


def route_after_stage(state) -> str:
    if state.get("status") == "halted":
        return "halt"
    if not state["last_result"]["passed"]:
        return "repair"    # only reachable for repairable stages (testing, security)
    return "request"       # go to the approval gate

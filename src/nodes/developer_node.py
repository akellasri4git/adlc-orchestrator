from .stage_wrapper import StageSpec


def _create_branch(state, tools):
    tools.codebase.ensure_branch(state["change_id"])


def _open_pr(state, tools):
    cid = state["change_id"]
    tools.codebase.open_pull_request(cid, f"ADLC: {cid}", "Opened by the ADLC Developer stage.")


DEVELOPER = StageSpec(
    name="developer", agent="general-purpose", skill="/coding-build",
    expected_outputs=["change-summary.json"], repairable=False,
    pre_hook=_create_branch, post_hook=_open_pr)

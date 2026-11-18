from .stage_wrapper import StageSpec

SECURITY = StageSpec(
    name="security", agent="security-review", skill="security-policy",
    expected_outputs=["security-report.sarif", "security-summary.md"],
    requires_pass_verdict=True, repairable=True)

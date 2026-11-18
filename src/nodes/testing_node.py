from .stage_wrapper import StageSpec

TESTING = StageSpec(
    name="testing", agent="general-purpose", skill="/testing-devsecops",
    expected_outputs=["ac-test-map.json", "test-report.xml", "coverage.json"],
    requires_pass_verdict=True, repairable=True)

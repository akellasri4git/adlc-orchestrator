from .stage_wrapper import StageSpec

REQUIREMENTS = StageSpec(
    name="requirements", agent="general-purpose", skill="/requirements-engineering",
    expected_outputs=["stories.md", "requirements.json"])

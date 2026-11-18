from .stage_wrapper import StageSpec

DESIGN = StageSpec(
    name="design", agent="general-purpose", skill="/architecture-design",
    expected_outputs=["design-contract.yaml"])  # ADR files are checked by Evidence & Traceability

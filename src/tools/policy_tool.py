"""Policy & Guardrails engine: allowed paths, approved commands, secret and PII checks.
Owned by another team. Verdicts are pass | warn | block."""


class StubPolicyTool:
    def screen_input(self, pack: dict) -> dict:
        return {"verdict": "pass"}  # prompt-injection screen on the context pack

    def issue_permissions(self, change_id: str, stage: str) -> dict:
        return {"verdict": "pass", "allowed_paths": ["src/", "tests/"], "approved_commands": ["build", "test"]}

    def screen_output(self, result: dict) -> dict:
        return {"verdict": "pass"}  # secret / PII scan on agent output

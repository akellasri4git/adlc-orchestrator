"""Wraps Copilot CLI in non-interactive mode. Used by every agent stage."""
import json
import subprocess


class CopilotCliTool:
    def __init__(self, command_template: list, timeout: int = 3600):
        self.command_template = command_template
        self.timeout = timeout

    def run(self, stage, agent, skill, context_pack, permissions, feedback="") -> dict:
        """Returns {outputs, verdict, findings, credits_used, ok}."""
        cmd = [part.format(agent=agent, skill=skill, context_pack=context_pack)
               for part in self.command_template]
        # TODO: pass permissions (allowed paths / approved commands) the way your CLI expects,
        # e.g. via flags or a policy file written next to the context pack.
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        if proc.returncode != 0:
            return {"ok": False, "outputs": {}, "findings": proc.stderr[-2000:], "credits_used": 0}
        # TODO: agree an output contract with the agent skills. Assumed here: JSON on stdout.
        return {"ok": True, **json.loads(proc.stdout)}


# Expected output files per stage (section 3.4 exit criteria)
STAGE_OUTPUTS = {
    "requirements": ["stories.md", "requirements.json"],
    "design": ["design-contract.yaml"],
    "developer": ["change-summary.json"],
    "testing": ["ac-test-map.json", "test-report.xml", "coverage.json"],
    "security": ["security-report.sarif", "security-summary.md"],
}


class StubCopilotCliTool:
    """Scripted stand-in. script={"testing": ["fail", "pass"]} gives a verdict per call."""

    def __init__(self, script: dict | None = None):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.calls = []

    def run(self, stage, agent, skill, context_pack, permissions, feedback="") -> dict:
        self.calls.append(stage)
        verdicts = self.script.get(stage)
        verdict = verdicts.pop(0) if verdicts else "pass"
        return {
            "ok": True, "verdict": verdict, "credits_used": 10,
            "findings": "" if verdict == "pass" else f"{stage} found problems",
            "outputs": {f: f".adlc/{stage}/{f}" for f in STAGE_OUTPUTS[stage]},
        }

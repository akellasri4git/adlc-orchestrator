"""Context Builder: assembles the context pack for each agent call.
Owned by another team. This is the interface the orchestrator expects."""
import hashlib
import json
from pathlib import Path


class StubContextBuilder:
    def __init__(self, workdir: str = "/tmp/adlc-packs"):
        self.dir = Path(workdir)

    def build(self, change_id, stage, skill, prior_outputs, feedback="") -> dict:
        pack = {"change_id": change_id, "stage": stage, "skill": skill,
                "prior": prior_outputs, "feedback": feedback}
        blob = json.dumps(pack, sort_keys=True)
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self.dir / f"{change_id}-{stage}.json"
        path.write_text(blob)
        return {"path": str(path), "hash": hashlib.sha256(blob.encode()).hexdigest()}

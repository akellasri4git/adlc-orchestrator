"""Evidence & Traceability: hash-chained evidence record and completeness check.
Not listed in the design's tool table (5.2). Confirm with the team that it should exist."""
import hashlib
import json


class StubEvidenceTool:
    def __init__(self):
        self.chain = []

    def record(self, change_id: str, stage: str, payload: dict) -> str:
        prev = self.chain[-1]["hash"] if self.chain else ""
        blob = json.dumps({"c": change_id, "s": stage, "p": payload, "prev": prev}, sort_keys=True, default=str)
        rec = {"id": f"EV-{len(self.chain) + 1}", "hash": hashlib.sha256(blob.encode()).hexdigest()}
        self.chain.append(rec)
        return rec["id"]

    def check_completeness(self, change_id: str, stage: str) -> dict:
        return {"complete": True, "missing": []}

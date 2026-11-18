"""Jira REST: read, comment, transition, remote link."""
import requests


class JiraTool:
    def __init__(self, base_url, token, ready_label, ready_status, gate_status):
        self.base, self.ready_label, self.ready_status = base_url.rstrip("/"), ready_label, ready_status
        self.gate_status = gate_status
        self.h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def is_ready(self, change_id: str) -> bool:
        r = requests.get(f"{self.base}/rest/api/3/issue/{change_id}?fields=labels,status", headers=self.h, timeout=30)
        r.raise_for_status()
        f = r.json()["fields"]
        return self.ready_label in f["labels"] and f["status"]["name"] == self.ready_status

    def comment(self, change_id: str, text: str) -> None:
        body = {"body": {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}]}}
        requests.post(f"{self.base}/rest/api/3/issue/{change_id}/comment",
                      headers=self.h, json=body, timeout=30).raise_for_status()

    def request_approval(self, change_id: str, stage: str, summary: str) -> None:
        self.comment(change_id, f"[ADLC] {stage} stage complete. Approval needed.\n{summary}")
        # TODO: look up the transition id for self.gate_status[stage] via
        # GET /issue/{key}/transitions, then POST /issue/{key}/transitions.


class StubJiraTool:
    def __init__(self):
        self.comments, self.approvals = [], []

    def is_ready(self, change_id): return True
    def comment(self, change_id, text): self.comments.append((change_id, text))
    def request_approval(self, change_id, stage, summary): self.approvals.append((change_id, stage))

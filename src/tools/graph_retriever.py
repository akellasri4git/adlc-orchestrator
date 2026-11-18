"""Knowledge-graph query API (licensed tool). Used by Context Builder and Evidence & Traceability."""
import requests


class GraphRetriever:
    def __init__(self, base_url, token):
        self.base, self.h = base_url.rstrip("/"), {"Authorization": f"Bearer {token}"}

    def slice_for(self, change_id: str, stage: str) -> dict:
        # TODO: replace with the real query endpoint of your graph tool.
        r = requests.get(f"{self.base}/slice", params={"change": change_id, "stage": stage},
                         headers=self.h, timeout=60)
        r.raise_for_status()
        return r.json()


class StubGraphRetriever:
    def slice_for(self, change_id, stage): return {"nodes": [], "links": []}

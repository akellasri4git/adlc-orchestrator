"""GitHub API and local workspace clone: branch creation and pull requests."""
import requests


class CodebaseTool:
    def __init__(self, api_url, repo, token):
        self.api, self.repo = api_url.rstrip("/"), repo
        self.h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    def ensure_branch(self, change_id: str, base: str = "main") -> str:
        branch = f"adlc/{change_id}"
        sha = requests.get(f"{self.api}/repos/{self.repo}/git/ref/heads/{base}",
                           headers=self.h, timeout=30).json()["object"]["sha"]
        r = requests.post(f"{self.api}/repos/{self.repo}/git/refs", headers=self.h, timeout=30,
                          json={"ref": f"refs/heads/{branch}", "sha": sha})
        if r.status_code not in (201, 422):  # 422 = already exists, fine on re-runs
            r.raise_for_status()
        return branch

    def open_pull_request(self, change_id: str, title: str, body: str, base: str = "main") -> str:
        r = requests.post(f"{self.api}/repos/{self.repo}/pulls", headers=self.h, timeout=30,
                          json={"title": title, "head": f"adlc/{change_id}", "base": base, "body": body})
        if r.status_code == 422:  # PR already open (repair loop)
            return "existing"
        r.raise_for_status()
        return r.json()["html_url"]


class StubCodebaseTool:
    def ensure_branch(self, change_id, base="main"): return f"adlc/{change_id}"
    def open_pull_request(self, change_id, title, body, base="main"): return f"https://example/pr/{change_id}"

"""Budget & Credit Policy ledger. Owned by another team."""


class StubBudgetTool:
    def __init__(self, total_credits: int = 10_000):
        self.remaining, self.records = total_credits, []

    def check(self, change_id: str, stage: str, headroom: int) -> dict:
        return {"allowed": self.remaining >= headroom, "remaining": self.remaining}

    def record(self, change_id: str, stage: str, credits: int) -> None:
        self.remaining -= credits
        self.records.append((change_id, stage, credits))

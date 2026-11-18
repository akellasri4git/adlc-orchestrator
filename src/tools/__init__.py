"""Tool bundle injected into nodes. Swap stubs for real implementations one at a time."""
from dataclasses import dataclass, field

from .budget_tool import StubBudgetTool
from .codebase_tool import StubCodebaseTool
from .context_builder_tool import StubContextBuilder
from .copilot_cli_tool import StubCopilotCliTool
from .evidence_tool import StubEvidenceTool
from .graph_retriever import StubGraphRetriever
from .jira_tool import StubJiraTool
from .policy_tool import StubPolicyTool


@dataclass
class Tools:
    copilot: object = field(default_factory=StubCopilotCliTool)
    jira: object = field(default_factory=StubJiraTool)
    codebase: object = field(default_factory=StubCodebaseTool)
    graph: object = field(default_factory=StubGraphRetriever)
    context: object = field(default_factory=StubContextBuilder)
    policy: object = field(default_factory=StubPolicyTool)
    budget: object = field(default_factory=StubBudgetTool)
    evidence: object = field(default_factory=StubEvidenceTool)


def stub_tools(**overrides) -> Tools:
    return Tools(**overrides)


def build_tools(settings) -> Tools:
    """Wire real implementations here as they become available."""
    from .codebase_tool import CodebaseTool
    from .copilot_cli_tool import CopilotCliTool
    from .jira_tool import JiraTool
    r = settings.raw
    return Tools(
        copilot=CopilotCliTool(r["copilot_cli"]["command"], r["copilot_cli"]["timeout_seconds"]),
        jira=JiraTool(r["jira"]["base_url"], settings.secret_from(r["jira"]["token_env"]),
                      r["jira"]["ready_label"], r["jira"]["ready_status"], r["jira"]["gate_status"]),
        codebase=CodebaseTool(r["github"]["api_url"], r["github"]["repo"],
                              settings.secret_from(r["github"]["token_env"])),
        # graph, context, policy, budget, evidence: still stubs until the owning teams deliver
    )

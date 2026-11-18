"""LangChain tool layer (section 5.2): exposes the tool classes as callable LangChain tools.
Use these where an agent or chain needs to call a tool by name."""
from langchain_core.tools import StructuredTool


def as_langchain_tools(tools) -> list:
    return [
        StructuredTool.from_function(
            func=tools.jira.comment, name="JiraTool",
            description="Comment on a Jira change request. Args: change_id, text."),
        StructuredTool.from_function(
            func=tools.graph.slice_for, name="GraphRetriever",
            description="Fetch the knowledge-graph slice for a change and stage."),
        StructuredTool.from_function(
            func=tools.codebase.ensure_branch, name="CodebaseTool",
            description="Create or reuse the adlc/<JIRA-KEY> change branch."),
    ]

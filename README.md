# ADLC Orchestrator (LangGraph)

Runs the five-stage ADLC pipeline as a LangGraph with approval gates, repair loops
and PostgreSQL checkpointing. All integrations start as stubs.

    pip install -r requirements.txt
    pytest                      # end-to-end flow with stubs, no external services
    export ADLC_POSTGRES_DSN=... ADLC_WEBHOOK_SECRET=... ADLC_JIRA_TOKEN=... ADLC_GITHUB_TOKEN=...
    python -m src.main

## Swap stubs for real components (src/tools/__init__.py: build_tools)
1. CopilotCliTool: confirm CLI flags and the agent output contract.
2. JiraTool: add the transition-id lookup in request_approval.
3. CodebaseTool: already usable against GitHub.
4. Context Builder, Policy, Budget, Evidence, Graph: wire in as the owning teams deliver.

## Decisions to confirm
- After a repair loop, Developer output goes back through the Code Review gate.
- Requirements/Design exit failures halt the run (no auto-repair defined in the design).
- Gate off-switch (gate_policy.yaml) needs Client team approval per section 5.1.

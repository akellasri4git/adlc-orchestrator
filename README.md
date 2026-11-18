# ADLC Orchestrator (LangGraph)

A Python service that runs a five-stage software delivery pipeline with human approval gates, repair loops, evidence tracking, and durable LangGraph checkpoints.

## Pipeline

```text
Requirements -> Approval -> Design -> Approval -> Developer -> Approval
    -> Testing -> Approval -> Security -> Approval -> Completed
```

Stages and their main outputs:

| Stage | Agent skill | Expected outputs |
|---|---|---|
| Requirements | `/requirements-engineering` | `stories.md`, `requirements.json` |
| Design | `/architecture-design` | `design-contract.yaml` |
| Developer | `/coding-build` | `change-summary.json` |
| Testing | `/testing-devsecops` | `ac-test-map.json`, `test-report.xml`, `coverage.json` |
| Security | `security-policy` | `security-report.sarif`, `security-summary.md` |

The Developer stage creates or reuses `adlc/<change-id>` and opens a pull request. Testing and security failures can route the run back to Developer. Repeated failures stop after the configured repair-loop limit.

## Prerequisites

- Python 3.10 or newer
- Git
- A macOS, Linux, or Windows terminal
- Optional for external integrations: Jira, GitHub, PostgreSQL, and the Copilot CLI

## 1. Clone and enter the repository

```bash
git clone https://github.com/akellasri4git/adlc-orchestrator.git
cd adlc-orchestrator
```

## 2. Create a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Run the test workflow

The tests use stub tools and an in-memory checkpointer, so they do not require Jira, GitHub, PostgreSQL, or an AI CLI.

```bash
pytest -v
```

The suite demonstrates:

- A complete run across all five stages
- Re-running a stage after `changes_requested`
- Routing testing failures back to Developer
- Stopping when the repair-loop limit is reached

## 5. Run the local demo API

Demo mode is isolated from external integrations:

```bash
cp .env.example .env
# .env should contain ADLC_MODE=mock
python -m src.main
```

In mock mode:

- No LLM or Copilot CLI call is made
- No Jira or GitHub API call is made
- The webhook secret defaults to `demo-secret`
- PostgreSQL is not used; memory checkpoints are used
- `ADLC_MOCK_SCRIPT` can make stages fail or pass predictably

For production:

```bash
ADLC_MODE=real
ADLC_POSTGRES_DSN=postgresql://...
ADLC_WEBHOOK_SECRET=your-long-random-secret
ADLC_JIRA_TOKEN=your-jira-token
ADLC_GITHUB_TOKEN=your-github-token
ADLC_HOST=0.0.0.0
ADLC_PORT=8080
```

The demo and production modes use the same LangGraph nodes, routing, gates, state, and HTTP API. Only tool implementations change, so no workflow rewrite is needed for promotion to production.

Open the interactive Swagger UI:

- http://127.0.0.1:8080/docs
- OpenAPI definition: http://127.0.0.1:8080/openapi.json

## 6. Start a demo run

Send:

```bash
curl -X POST http://127.0.0.1:8080/runs \
  -H 'Content-Type: application/json' \
  -d '{"change_id":"CHANGE-DEMO"}'
```

The run pauses at the first gate. This is the stub demo behavior; no Jira approval is required automatically.

## 7. Approve a demo gate

Approval webhooks must contain a HMAC SHA-256 signature. The demo secret is `demo-secret`.

macOS/Linux:

```bash
BODY='{"change_id":"CHANGE-DEMO","stage":"requirements","decision":"approved","comments":""}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac 'demo-secret' | sed 's/^.* //')

curl -X POST http://127.0.0.1:8080/webhooks/jira \
  -H 'Content-Type: application/json' \
  -H "X-Hub-Signature-256: sha256=$SIG" \
  -d "$BODY"
```

Repeat the same request using each stage name:

- `requirements`
- `design`
- `developer`
- `testing`
- `security`

To request a change instead:

```json
{
  "change_id": "CHANGE-DEMO",
  "stage": "requirements",
  "decision": "changes_requested",
  "comments": "Fix acceptance criterion AC-2"
}
```

The stage will run again and preserve the comments as feedback.

## Running with the production entry point

Set the required environment variables:

```bash
export ADLC_POSTGRES_DSN='postgresql://user:password@host:5432/adlc'
export ADLC_WEBHOOK_SECRET='replace-with-a-long-random-secret'
export ADLC_JIRA_TOKEN='replace-with-the-Jira-token'
export ADLC_GITHUB_TOKEN='replace-with-the-GitHub-token'

python -m src.main
```

The service listens on `0.0.0.0:8080`.

PostgreSQL enables durable checkpointing. Without `ADLC_POSTGRES_DSN`, the application uses an in-memory checkpointer and state is lost when the process stops.

## Configuration

### `config/settings.yaml`

Contains:

- Repair-loop limit
- PostgreSQL and webhook environment-variable names
- Jira labels, statuses, and gate statuses
- GitHub API and repository settings
- Copilot CLI command template and timeout
- Credit headroom for each stage

Secret values are not stored in this file. They are read from environment variables.

### `config/gate_policy.yaml`

Controls whether each approval gate is enabled:

```yaml
gates:
  requirements: true
  design: true
  developer: true
  testing: true
  security: true
```

Gates fail safe: an omitted or unknown stage gate is enabled unless the configuration explicitly disables it. Disabling a gate requires the appropriate client/team approval.

## Architecture

- `src/main.py` loads configuration, builds tools and the graph, then starts FastAPI.
- `src/graph.py` defines the LangGraph stages and conditional routes.
- `src/state.py` defines the run state shared between nodes.
- `src/nodes/stage_wrapper.py` performs entry checks, context preparation, policy screening, agent execution, exit checks, and evidence recording.
- `src/gates.py` pauses runs with LangGraph interrupts and resumes them through webhooks.
- `src/webhook.py` provides `/runs` and signed `/webhooks/jira` endpoints.
- `src/checkpointing.py` selects PostgreSQL or in-memory checkpointing.
- `src/tools/` contains tool integrations and their local stubs.

## Integration status

| Component | Status |
|---|---|
| LangGraph pipeline | Implemented |
| FastAPI endpoints | Implemented |
| Approval interrupts | Implemented |
| Testing/security repair loops | Implemented |
| PostgreSQL checkpointing | Implemented |
| GitHub branch and pull-request API | Implemented |
| Jira comments and readiness checks | Implemented |
| Jira gate transitions | TODO: resolve transition IDs |
| Copilot CLI | Wrapper implemented; output contract must be confirmed |
| Context Builder | Stub |
| Policy engine | Stub |
| Budget ledger | Stub |
| Evidence and traceability | Stub |
| Graph retriever | Stub |

## Current integration limitation

External components are intentionally not all production-ready. `build_tools()` in `src/tools/__init__.py` combines real GitHub/Jira/Copilot implementations with the remaining stubs.

Before using real external systems:

1. Confirm Copilot CLI flags and JSON stdout contract.
2. Implement Jira transition-ID lookup for each gate status.
3. Replace the context, policy, budget, evidence, and graph stubs.
4. Configure Jira Automation to call the signed webhook endpoint.
5. Put the service behind HTTPS and restrict network access.
6. Use a secret manager rather than shell environment variables for production secrets.

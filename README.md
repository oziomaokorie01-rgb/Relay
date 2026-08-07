# Relay

**Collaborative operational memory for AI agents built around DataHub context.**

Relay is a multi-agent data incident investigation system that helps AI agents investigate data problems, propose repairs, verify evidence, preserve approved resolutions, and reuse that knowledge in future investigations.

Instead of allowing incident knowledge to disappear after a problem is fixed, Relay turns verified investigations into reusable organizational memory.

> Every verified investigation should make the next investigation easier.

---

## The Problem

AI agents working with organizational data often lack the context needed to make reliable decisions.

A dashboard may suddenly report incorrect revenue, but understanding why can require knowledge of:

- upstream datasets
- schemas
- lineage
- ownership
- recent metadata changes
- downstream dependencies
- previous incidents

DataHub provides this organizational context.

Relay builds an operational reasoning and memory layer around that context.

---

## How Relay Works

A Relay investigation moves through a collaborative agent workflow:

```text
DataHub Context
      |
      v
Investigator Agent
      |
      v
Repair Agent
      |
      v
Reviewer Agent
      |
      v
Human Approval
      |
      v
Archivist Agent
      |
      v
Verified Relay Memory
      |
      v
Future Investigation Reuse
```

### 1. Investigator Agent

The Investigator examines available asset metadata, lineage, schema information, and incident context.

It produces:

- root-cause hypotheses
- supporting evidence
- affected assets
- confidence scores

### 2. Repair Agent

The Repair Agent converts the investigation into an actionable repair proposal.

Repairs can include:

- SQL fixes
- schema normalization
- pipeline corrections
- validation recommendations
- remediation steps

### 3. Reviewer Agent

The Reviewer independently evaluates the proposed repair.

It checks:

- whether evidence supports the root cause
- whether the repair addresses that cause
- whether important evidence is missing
- downstream risk
- confidence

### 4. Human Approval

High-impact organizational knowledge should not automatically become trusted memory.

Relay therefore supports an explicit human approval step before a resolution is treated as verified organizational knowledge.

### 5. Archivist Agent

After approval, the Archivist converts the completed investigation into structured reusable memory.

The memory preserves:

- root cause
- resolution
- evidence
- affected assets
- confidence
- reusable guidance

### 6. Memory Reuse

Future investigations can retrieve relevant verified memories.

Instead of rediscovering the same failure from scratch, an agent can inherit knowledge from previous investigations and begin with an already-verified repair pattern.

---

# DataHub Integration

Relay is designed around DataHub as its organizational context layer.

The DataHub integration uses a provider abstraction so the investigation system does not depend on one retrieval implementation.

```text
                    DataHubGateway
                         |
              +----------+----------+
              |                     |
              v                     v
     MockDataHubGateway     GraphQLDataHubGateway
              |                     |
              v                     v
    Deterministic Demo       DataHub Deployment
        Context                  Context
```

The normalized gateway supports operations such as:

- asset search
- asset metadata retrieval
- ownership context
- schema context
- upstream/downstream lineage

## Hosted Demo Mode

The hosted Relay demo currently uses deterministic DataHub-compatible fixtures.

This allows judges to run a predictable end-to-end investigation without requiring credentials for an external DataHub deployment.

The fixtures model realistic DataHub concepts including:

- DataHub URNs
- datasets
- dashboards
- platforms
- ownership
- schemas
- lineage
- metadata

## Live DataHub Provider

The repository also contains a configurable GraphQL DataHub gateway intended for connecting Relay to a DataHub deployment.

Configuration is environment-based:

```env
DATAHUB_PROVIDER=graphql
DATAHUB_BASE_URL=<datahub-instance>
DATAHUB_TOKEN=<access-token>
DATAHUB_TIMEOUT_SECONDS=20
```

For deterministic demo mode:

```env
DATAHUB_PROVIDER=mock
```

No credentials are committed to this repository.

> Note: The public hackathon demo currently runs in deterministic demo mode. The GraphQL provider represents Relay's live DataHub integration path, but it has not yet been validated against a production DataHub instance.

---

# Example Incident

A sample investigation is included in:

```text
examples/revenue-dashboard-incident/
```

Scenario:

> The Revenue Dashboard suddenly reports 35% less revenue after a refresh.

Relay receives context representing the dashboard's upstream lineage and discovers a schema change:

```text
raw.raw_orders
      |
      v
analytics.clean_orders
      |
      v
analytics.revenue_model
      |
      v
Revenue Dashboard
```

`customer_id` changed from:

```text
integer -> string
```

The downstream transformation still expected an integer join key.

Relay connects the schema change to the failed joins, proposes a normalization repair, reviews the evidence, requests human approval, and archives the verified resolution.

A later investigation encountering a similar schema mismatch can reuse that memory.

Sample artifacts:

```text
01-datahub-context.json
02-investigation-result.json
03-repair-proposal.sql
04-review-and-approval.json
05-archived-memory.json
```

---

# Core Features

- Multi-agent incident investigation
- DataHub-oriented metadata context
- Asset search and inspection
- Lineage-aware reasoning
- Evidence tracking
- Root-cause analysis
- Repair proposals
- Independent agent review
- Confidence scoring
- Human approval workflow
- Investigation activity timeline
- Verified organizational memory
- Memory reuse
- DataHub provider abstraction
- Deterministic hackathon demo mode
- Configurable GraphQL DataHub gateway
- Responsive web interface

---

# Architecture

```text
                        Relay Frontend
                              |
                              v
                         FastAPI API
                              |
                              v
                    Investigation Service
                              |
            +-----------------+-----------------+
            |                 |                 |
            v                 v                 v
      Investigator          Repair           Reviewer
            |                 |                 |
            +-----------------+-----------------+
                              |
                              v
                       Human Approval
                              |
                              v
                          Archivist
                              |
                  +-----------+-----------+
                  |                       |
                  v                       v
            Relay Memory            DataHub Gateway
                                          |
                              +-----------+-----------+
                              |                       |
                              v                       v
                             Mock                  GraphQL
```

---

# Technology

## Backend

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite / async database access
- HTTPX
- Server-Sent Events
- DataHub provider abstraction

## Frontend

- React
- TypeScript
- Vite
- Responsive CSS

## Deployment

Relay is structured as separate frontend and backend services.

The backend exposes REST APIs under:

```text
/api/v1
```

---

# Important API Routes

## Investigations

```text
POST /api/v1/investigations
GET  /api/v1/investigations
GET  /api/v1/investigations/{id}

POST /api/v1/investigations/{id}/run
GET  /api/v1/investigations/{id}/activity
GET  /api/v1/investigations/{id}/evidence
GET  /api/v1/investigations/{id}/repair
GET  /api/v1/investigations/{id}/review

POST /api/v1/investigations/{id}/approval
POST /api/v1/investigations/{id}/archive

GET /api/v1/investigations/{id}/memory-reuse
```

## Assets

```text
GET /api/v1/assets/search
GET /api/v1/assets/{encoded_urn}
GET /api/v1/assets/{encoded_urn}/lineage
```

## Memories

```text
GET /api/v1/memories
GET /api/v1/memories/{memory_id}
GET /api/v1/memories/{memory_id}/reuse
```

---

# Local Development

## Backend

From the repository root:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy the environment template:

```bash
copy .env.example .env
```

Start Relay:

```bash
uvicorn app.main:app --reload
```

The backend runs locally at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The development frontend normally runs at:

```text
http://localhost:5173
```

Configure the frontend API endpoint when necessary:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

# Running the Deterministic Demo

Use:

```env
DATAHUB_PROVIDER=mock
```

Start the backend and frontend.

Then:

1. Search for a DataHub-style asset.
2. Select an affected asset.
3. Create an investigation.
4. Run the investigation.
5. Inspect the evidence.
6. Review the proposed repair.
7. Inspect the Reviewer decision.
8. Approve the investigation.
9. Archive the verified result.
10. Inspect the resulting organizational memory.
11. Test memory reuse against a related investigation.

---

# Repository Structure

```text
Relay/
|
+-- backend/
|   +-- app/
|       +-- agents/
|       +-- api/
|       +-- core/
|       +-- database/
|       +-- integrations/
|       |   +-- datahub/
|       +-- models/
|       +-- orchestration/
|       +-- repositories/
|       +-- schemas/
|       +-- services/
|
+-- frontend/
|   +-- src/
|
+-- examples/
|   +-- revenue-dashboard-incident/
|
+-- LICENSE
+-- README.md
```

---

# Current Limitations

Relay is a hackathon prototype rather than a production incident-management system.

Current limitations include:

- the hosted demo uses deterministic DataHub-compatible fixtures
- the GraphQL provider has not yet been validated against a live DataHub deployment
- automatic write-back of verified Relay memories into a live DataHub graph remains future integration work
- production authentication and authorization are outside the current prototype scope

These boundaries are intentionally documented so the demo clearly distinguishes implemented behavior from planned integration work.

---

# Roadmap

Future work includes:

- validating the GraphQL provider against a live DataHub deployment
- DataHub MCP Server / Agent Context Kit support
- writing verified incident knowledge back into DataHub
- richer metadata change detection
- additional repair artifact generation
- organization-level access controls
- agent evaluation and observability
- cross-team memory sharing

---

# Why Relay

Data platforms already capture what data exists.

AI agents also need to understand:

> What happened here before, what fixed it, and can I trust that solution?

Relay turns resolved incidents into inherited operational knowledge.

**DataHub provides the organizational context. Relay makes the lessons learned from acting on that context reusable.**

---

# License

Relay is open source under the **Apache License 2.0**.

---

# Hackathon

Built for **Build with DataHub: The Agent Hackathon**.

Primary challenge:

**Agents That Do Real Work**
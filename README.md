# COMPASS

**C**ompliance **M**apping and **P**olicy **A**ssessment **S**peech **S**ystem

> A FedRAMP compliance voice agent powered by Gemini 2.5 Flash Native Audio.  
> Submitted to the **Gemini Live Agent Challenge** — *Live Agents* category.

---

## Overview

COMPASS lets security architects describe their system out loud and receive real-time NIST SP 800-53 Rev 5 control mapping, gap analysis, and OSCAL document generation — all driven by a bidirectional audio session with Gemini.

Key capabilities:

| Feature | Detail |
|---|---|
| **Voice-first UX** | Gemini Live API — interruptible, bidirectional PCM audio |
| **Vision analysis** | Architecture diagrams analyzed via Gemini multimodal input |
| **FIPS 199 classification** | Automated confidentiality / integrity / availability impact scoring |
| **800-53 control mapping** | Semantic RAG over full Rev 5 catalog (Vertex AI Vector Search) |
| **Gap analysis** | Heuristic gap detection with remediation hints and effort estimates |
| **OSCAL output** | OSCAL 1.1.2 SSP + POA&M + Assessment Results, uploaded to GCS |
| **MITRE ATLAS** | AI/ML threat technique → mitigating control lookup |

---

## Architecture

```
Browser (React + WebAudio) 
    │ PCM 16kHz / JSON events
    ▼
FastAPI (Cloud Run) — /ws/live
    │ google-genai Live API
    ▼
Gemini 2.5 Pro Live
    │ function_calls
    ▼
ADK Sub-agents (classify / map / gap / oscal)
    │
    ├── Vertex AI Vector Search  (control RAG)
    ├── Cloud Firestore          (session state)
    └── Cloud Storage            (OSCAL outputs)
```

See [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md) for the full system design.

---

## Hackathon Compliance

| Requirement | Status |
|---|---|
| Google Gemini model | ✅ `gemini-2.5-pro` via Vertex AI |
| Google ADK or GenAI SDK | ✅ Both — `google-adk` (agents) + `google-genai` (Live API) |
| Google Cloud hosting | ✅ Cloud Run + Firestore + GCS + Vertex AI |
| Live API / interruptible | ✅ Bidirectional audio via `genai.Client.aio.live.connect()` |
| Public deployment | ✅ Cloud Run public endpoint |
| README | ✅ This file |
| Architecture diagram | ✅ See `docs/architecture.png` |
| Demo video | 📹 See submission link |
| Terraform IaC | ✅ `terraform/` directory |
| Blog post | 📝 Planned |

---

## Project Structure

```
COMPASS/
├── backend/
│   ├── app.py              # FastAPI + WebSocket entrypoint
│   ├── config.py           # Pydantic Settings
│   ├── models/             # Pydantic data models
│   ├── tools/              # ADK FunctionTools (classify, map, gap, OSCAL, …)
│   ├── services/           # Firestore, GCS, Vector Search clients
│   ├── agents/             # ADK root agent + 4 sub-agents
│   └── knowledge/          # NIST 800-53, MITRE ATLAS, FedRAMP corpora
├── frontend/               # React + TypeScript (Vite)
├── terraform/              # IaC — Cloud Run, Firestore, GCS, Artifact Registry
├── tests/                  # Pytest unit + integration tests
├── Dockerfile
├── cloudbuild.yaml
├── requirements.txt
├── .env.example
├── ARCHITECTURE_PLAN.md
├── FRONTEND_DESIGN_SPEC.md
└── BUILD_PLAN.md
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- Node 20+ (for frontend)
- Google Cloud project with APIs enabled (see below)
- Application Default Credentials: `gcloud auth application-default login`

### Required GCP APIs

```bash
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com
```

### Backend

```bash
# 1. Clone and enter project
git clone <repo-url>
cd COMPASS

# 2. Create virtualenv
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your GCP project, bucket names, etc.

# 5. Run development server
ENV=development python -m uvicorn backend.app:app --reload --port 8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Running Tests

Unit tests run fully offline — no GCP credentials, no network access required.

```bash
# 1. Activate virtualenv (if not already)
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run unit tests
ENV=test pytest tests/ -v --ignore=tests/test_integration.py
```

Expected output: all tests in `tests/test_classifier.py`, `tests/test_mapper.py`, and `tests/test_oscal_generator.py` pass. No environment variables or credentials needed.

```bash
# Run a specific test file
ENV=test pytest tests/test_classifier.py -v

# Run with short traceback on failure
ENV=test pytest tests/ -v --tb=short --ignore=tests/test_integration.py
```

### Integration Tests

Integration tests require live GCP credentials and a provisioned project:

```bash
# Authenticate
gcloud auth application-default login

# Set required environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export FIRESTORE_DATABASE=compass
export GCS_BUCKET_OSCAL=your-bucket-name

# Run integration tests
ENV=test pytest tests/test_integration.py -v
```

---

## Deployment

### Docker (local validation)

```bash
docker build -t compass-backend .
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=compass-fedramp \
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  compass-backend
```

### Cloud Run (manual)

```bash
gcloud run deploy compass-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8080
```

### Terraform (recommended)

```bash
cd terraform
terraform init
terraform plan -var="project_id=compass-fedramp"
terraform apply -var="project_id=compass-fedramp"
```

### Cloud Build (CI/CD)

Push to `main` branch triggers the Cloud Build pipeline defined in `cloudbuild.yaml`:
lint → test → build → push to Artifact Registry → deploy to Cloud Run.

---

## Environment Variables

See [.env.example](.env.example) for a full reference.

Key variables:

| Variable | Description | Default |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `compass-fedramp` |
| `GEMINI_MODEL` | Gemini text model name | `gemini-2.5-pro` |
| `GEMINI_LIVE_MODEL` | Gemini Live API model | `gemini-2.5-flash-native-audio-latest` |
| `GEMINI_VOICE` | TTS voice | `Kore` |
| `FIRESTORE_DATABASE` | Firestore database name | `compass` |
| `GCS_BUCKET_OSCAL` | GCS bucket for OSCAL outputs | `compass-fedramp-oscal` |
| `VECTOR_SEARCH_INDEX_ENDPOINT_ID` | Vertex AI index endpoint | — |

---

## WebSocket Protocol

Connect to `wss://<host>/ws/live`.

**1. Send init frame (JSON):**
```json
{ "session_id": "optional-existing-id", "user_id": "user@example.com" }
```

**2. Stream PCM audio (binary frames):**
16kHz mono 16-bit PCM from `getUserMedia()`.

**3. Receive audio back (binary frames):**
24kHz PCM from Gemini — pipe to Web Audio API.

**4. Receive structured events (JSON frames):**
```json
{ "type": "classification", "data": { "overall_impact": "Moderate", ... } }
{ "type": "control_mapped", "data": { "control_id": "SC-7", ... } }
{ "type": "gap_found", "data": { "risk_level": "high", ... } }
{ "type": "oscal_ready", "data": { "document_type": "ssp", "gcs_path": "..." } }
{ "type": "transcript", "speaker": "compass", "text": "...", "final": true }
```

---

## License

Source-available — free for government, personal, academic, and research use. Commercial use requires a paid license. See [LICENSE](LICENSE) for full terms or contact info@eucann.life.

---

## Team

Built for the **Gemini Live Agent Challenge** by the euCann Software Development team.

# COMPASS — Bill of Materials (BOM)

> This document serves as both the **Software Bill of Materials (SBOM)** and the
> **AI Bill of Materials (AIBOM)** for the COMPASS system.

| | |
|---|---|
| **System** | COMPASS |
| **Version** | See git tag / `cloudbuild.yaml` |
| **Format** | Human-readable Markdown (machine-readable CycloneDX JSON planned) |
| **Last Updated** | 2026-06-22 |

---

## Table of Contents

1. [AI Bill of Materials (AIBOM)](#1-ai-bill-of-materials-aibom)
2. [Software Bill of Materials (SBOM)](#2-software-bill-of-materials-sbom)
   - [Backend — Python](#21-backend--python)
   - [Frontend — JavaScript / TypeScript](#22-frontend--javascript--typescript)
3. [Knowledge Corpora & Datasets](#3-knowledge-corpora--datasets)
4. [Infrastructure & Cloud Services](#4-infrastructure--cloud-services)

---

## 1. AI Bill of Materials (AIBOM)

### 1.1 Foundation Models

| Model ID | Provider | API Surface | Role in COMPASS | Modalities |
|---|---|---|---|---|
| `gemini-2.5-flash-native-audio-latest` | Google DeepMind (via Gemini Developer API) | `google-genai` Live API | Primary Live session — bidirectional PCM audio, real-time turn-taking, interruptible conversation | Text, Audio, Vision |
| `gemini-2.5-pro` | Google DeepMind (via Gemini Developer API / Vertex AI) | `google-genai` / `google-adk` | All four ADK sub-agents (classify, map, gap, oscal) and post-turn orchestration | Text, Vision |
| `text-embedding-005` | Google (Vertex AI) | `google-cloud-aiplatform` / `vertexai` | Embedding generation for control RAG queries against Vertex AI Vector Search | Text |

### 1.2 AI Agents & Orchestration

| Component | File | Framework | Description |
|---|---|---|---|
| Root Agent | `backend/agents/root_agent.py` | Google ADK | Top-level orchestrator; routes requests to sub-agents via function calls |
| Classifier Agent | `backend/agents/classifier_agent.py` | Google ADK | Assigns FIPS 199 impact levels (C / I / A) based on system description |
| Mapper Agent | `backend/agents/mapper_agent.py` | Google ADK | Maps NIST SP 800-53 Rev 5 controls to described system components |
| Gap Agent | `backend/agents/gap_agent.py` | Google ADK | Detects control gaps, estimates remediation effort |
| OSCAL Agent | `backend/agents/oscal_agent.py` | Google ADK | Generates OSCAL 1.1.2 SSP, POA&M, and Assessment Results |

### 1.3 AI-Backed Services & Tools

| Service / Tool | File | Description |
|---|---|---|
| Vector Search service | `backend/services/vector_service.py` | Generates query embeddings; queries Vertex AI Vector Search for nearest-neighbor control retrieval |
| Control Lookup tool | `backend/tools/control_lookup.py` | ADK FunctionTool wrapping control RAG |
| Gap Analyzer tool | `backend/tools/gap_analyzer.py` | Heuristic gap detection driven by LLM outputs |
| Threat Lookup tool | `backend/tools/threat_lookup.py` | MITRE ATLAS technique → mitigating control lookup |
| OSCAL Generator tool | `backend/tools/oscal_generator.py` | Structures LLM-produced mappings into OSCAL 1.1.2 artifacts |
| OSCAL Validator tool | `backend/tools/oscal_validator.py` | Validates generated OSCAL against schema |
| Classify System tool | `backend/tools/classify_system.py` | FIPS 199 / NIST 800-60 classification helper |
| Input Sanitizer | `backend/security/input_sanitizer.py` | OWASP LLM Top 10 prompt-injection hardening applied to all LLM inputs |

### 1.4 AI Safety & Guardrails

| Control | Implementation |
|---|---|
| Prompt injection mitigation (OWASP LLM01) | `InputSanitizer` applied to all user-supplied text before LLM input |
| Excessive agency limits (OWASP LLM06 / Agentic Top 10) | `require_session_ownership_check`, `tool_execution_timeout_seconds = 30` |
| Resource exhaustion (OWASP LLM10) | `max_diagram_size_mb = 10`, `max_sessions_per_user = 20`, per-route rate limits |
| Low-confidence flagging | Mapper and gap agents flag uncertain results for human review |
| Human-in-the-loop | All OSCAL output requires explicit user request; no autonomous submission |

### 1.5 AI Model Governance

| Item | Detail |
|---|---|
| Training data transparency | Models used as-is from Google; no fine-tuning performed |
| Data sent to models | User voice/text descriptions and optionally uploaded architecture diagrams |
| PII handling | Sessions are user-scoped; transcripts stored in Firestore with 15-minute inactivity timeout |
| Output validation | OSCAL artifacts validated against schema before upload to GCS |
| Auditability | Full session transcript retained in Firestore per session |

---

## 2. Software Bill of Materials (SBOM)

### 2.1 Backend — Python

**Runtime:** Python 3.12+

| Package | Version Constraint | License | Purpose |
|---|---|---|---|
| `google-genai` | ≥1.0.0 | Apache-2.0 | Gemini Developer API client (Live API, generate content) |
| `google-adk` | ≥0.4.0 | Apache-2.0 | Agent Development Kit — ADK agent / sub-agent framework |
| `google-cloud-firestore` | ≥2.16.0 | Apache-2.0 | Session state persistence |
| `google-cloud-storage` | ≥2.16.0 | Apache-2.0 | OSCAL artifact upload / retrieval |
| `google-cloud-aiplatform` | ≥1.57.0 | Apache-2.0 | Vertex AI Vector Search + embedding API |
| `vertexai` | ≥1.0.0 | Apache-2.0 | Vertex AI SDK (embedding model loading) |
| `fastapi` | ≥0.111.0 | MIT | HTTP + WebSocket server |
| `uvicorn[standard]` | ≥0.29.0 | BSD-3-Clause | ASGI server |
| `python-multipart` | ≥0.0.9 | Apache-2.0 | File / diagram upload parsing |
| `websockets` | ≥12.0 | BSD-3-Clause | WebSocket support |
| `pydantic` | ≥2.7.0 | MIT | Data validation and settings |
| `pydantic-settings` | ≥2.3.0 | MIT | Environment-variable settings |
| `python-jose[cryptography]` | ≥3.3.0 | MIT | JWT token handling |
| `firebase-admin` | ≥6.5.0 | Apache-2.0 | Firebase / Firestore admin operations |
| `httpx` | ≥0.27.0 | BSD-3-Clause | Async HTTP client |
| `aiofiles` | ≥23.2.1 | Apache-2.0 | Async file I/O |
| `pytest` | ≥8.2.0 | MIT | Test framework |
| `pytest-asyncio` | ≥0.23.7 | Apache-2.0 | Async test support |
| `pytest-mock` | ≥3.14.0 | MIT | Mock helpers for tests |
| `ruff` | ≥0.4.0 | MIT | Linter / formatter |

### 2.2 Frontend — JavaScript / TypeScript

**Runtime:** Node 20+ · React 18 · TypeScript 5 · Vite 5

#### Production Dependencies

| Package | Version Constraint | License | Purpose |
|---|---|---|---|
| `react` | ^18.3.1 | MIT | UI framework |
| `react-dom` | ^18.3.1 | MIT | React DOM renderer |
| `react-router-dom` | ^6.30.1 | MIT | Client-side routing |
| `@tanstack/react-query` | ^5.83.0 | MIT | Server-state / async data management |
| `react-hook-form` | ^7.61.1 | MIT | Form state management |
| `@hookform/resolvers` | ^3.10.0 | MIT | Zod integration for react-hook-form |
| `zod` | ^3.25.76 | MIT | Schema validation |
| `recharts` | ^2.15.4 | MIT | Data visualization charts |
| `lucide-react` | ^0.462.0 | ISC | Icon library |
| `next-themes` | ^0.3.0 | MIT | Dark/light theme management |
| `sonner` | ^1.7.4 | MIT | Toast notifications |
| `date-fns` | ^3.6.0 | MIT | Date utilities |
| `embla-carousel-react` | ^8.6.0 | MIT | Carousel component |
| `cmdk` | ^1.1.1 | MIT | Command palette |
| `vaul` | ^0.9.9 | MIT | Drawer component |
| `input-otp` | ^1.4.2 | MIT | OTP input component |
| `react-day-picker` | ^8.10.1 | MIT | Date picker |
| `react-resizable-panels` | ^2.1.9 | MIT | Resizable panel layouts |
| `class-variance-authority` | ^0.7.1 | Apache-2.0 | Variant-based CSS class management |
| `clsx` | ^2.1.1 | MIT | Conditional CSS class utility |
| `tailwind-merge` | ^2.6.0 | MIT | Tailwind class merging |
| `tailwindcss-animate` | ^1.0.7 | MIT | Tailwind animation utilities |
| `@radix-ui/*` (22 primitives) | ^1.x – ^2.x | MIT | Accessible headless UI components |

#### Development Dependencies

| Package | Version Constraint | License | Purpose |
|---|---|---|---|
| `vite` | ^5.4.19 | MIT | Build tool and dev server |
| `@vitejs/plugin-react-swc` | ^3.11.0 | MIT | SWC-based React transform |
| `typescript` | ^5.8.3 | Apache-2.0 | TypeScript compiler |
| `typescript-eslint` | ^8.38.0 | MIT | TypeScript ESLint rules |
| `eslint` | ^9.32.0 | MIT | Linter |
| `eslint-plugin-react-hooks` | ^5.2.0 | MIT | React hooks lint rules |
| `eslint-plugin-react-refresh` | ^0.4.20 | MIT | HMR lint rules |
| `tailwindcss` | ^3.4.17 | MIT | Utility-first CSS framework |
| `@tailwindcss/typography` | ^0.5.16 | MIT | Prose typography plugin |
| `autoprefixer` | ^10.4.21 | MIT | PostCSS vendor prefixes |
| `postcss` | ^8.5.6 | MIT | CSS transformation pipeline |
| `vitest` | ^3.2.4 | MIT | Unit test runner |
| `@testing-library/react` | ^16.0.0 | MIT | React component testing |
| `@testing-library/jest-dom` | ^6.6.0 | MIT | DOM assertion matchers |
| `jsdom` | ^20.0.3 | MIT | DOM simulation for tests |
| `lovable-tagger` | ^1.1.13 | MIT | Build-time component tagging |
| `globals` | ^15.15.0 | MIT | Global variable definitions for ESLint |
| `@types/node` | ^22.16.5 | MIT | Node.js type definitions |
| `@types/react` | ^18.3.23 | MIT | React type definitions |
| `@types/react-dom` | ^18.3.7 | MIT | React DOM type definitions |

---

## 3. Knowledge Corpora & Datasets

These datasets are bundled in `backend/knowledge/` and used for RAG and
classification at runtime. They are **not** used to train or fine-tune any model.

| Dataset | Path | Source | Version / Description |
|---|---|---|---|
| NIST SP 800-53 Rev 5 Control Catalog | `backend/knowledge/nist_800_53_rev5/nist_800_53_rev5_catalog.json` | NIST (public domain) | Full control catalog — basis for all control mapping |
| NIST SP 800-60 Information Types | `backend/knowledge/nist_800_60/information_types.json` | NIST (public domain) | Information type taxonomy used for FIPS 199 classification |
| FedRAMP Rev 5 Baselines | `backend/knowledge/fedramp/` (4 files) | FedRAMP PMO (public domain) | Low, Moderate, High, and LI-SaaS control baselines |
| MITRE ATLAS Techniques | `backend/knowledge/mitre_atlas/atlas_techniques.json` | MITRE (CC BY 4.0) | AI/ML adversarial technique taxonomy for AI-system threat mapping |

---

## 4. Infrastructure & Cloud Services

| Service | Provider | Purpose |
|---|---|---|
| Cloud Run | Google Cloud | Hosts the FastAPI backend container |
| Cloud Build | Google Cloud | CI/CD — builds and deploys on push to `main` |
| Artifact Registry | Google Cloud | Container image storage |
| Cloud Firestore | Google Cloud | Session state and transcript persistence |
| Cloud Storage (GCS) | Google Cloud | OSCAL artifact storage and retrieval |
| Vertex AI Vector Search | Google Cloud | Approximate nearest-neighbor control retrieval (RAG index) |
| Vertex AI (Embeddings) | Google Cloud | `text-embedding-005` embedding generation |
| Gemini Developer API | Google | Live audio API (`gemini-2.5-flash-native-audio-latest`) and generate content |
| Firebase Auth | Google | User authentication and session ownership |

---

## 5. Provenance & Reproducibility

- **Backend:** Pin exact versions with `pip-compile` / `pip freeze` for production
  deployments. This file tracks minimum version constraints as declared in
  `requirements.txt`.
- **Frontend:** Exact resolved versions are locked in `frontend/package-lock.json`
  (or `pnpm-lock.yaml`).
- **Models:** Used via Google-managed APIs; model identifiers pinned in
  `backend/config.py`. Google may update `*-latest` aliases — pin to a fixed
  version for regulated deployments.
- **Knowledge corpora:** Bundled at repository commit; version/source noted above.
  Update corpora when NIST or FedRAMP publish new revisions.

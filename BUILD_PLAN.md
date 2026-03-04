# FedRAMP Compliance Voice Agent — Build Plan

## Gemini Live Agent Challenge | Category: Live Agents 🗣️

---

## 1. The Pitch (30 seconds)

**Problem:** Security architects spend 40–80 hours manually mapping system descriptions to NIST SP 800-53 controls for FedRAMP authorization. They toggle between dozens of PDFs, spreadsheets, and OSCAL templates — a process that's error-prone, slow, and inaccessible to non-specialists.

**Solution:** **COMPASS** (**CO**mpliance **M**apping & **P**olicy **A**ssessment **S**peech **S**ystem) — a real-time voice agent that _listens_ to a security architect describe their system, _sees_ architecture diagrams and screenshots via vision, dynamically maps descriptions to NIST 800-53 controls, asks clarifying questions, flags compliance gaps, and generates OSCAL-formatted output — all through natural conversation.

**Value:** Compresses weeks of compliance mapping into a single voice session. Democratizes FedRAMP expertise. Produces machine-readable OSCAL output ready for 3PAO review.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Web UI       │  │  Voice I/O   │  │  Architecture      │    │
│  │  (React/Next) │  │  (Mic/Speaker│  │  Diagram Upload    │    │
│  │              │  │   via Live API│  │  (Vision Input)    │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘    │
│         │                 │                    │                │
│         └─────────────────┼────────────────────┘                │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │              Gemini Live API (WebSocket)                  │   │
│  │   • Audio streaming (bidirectional)                      │   │
│  │   • Vision input (architecture diagrams, screenshots)    │   │
│  │   • Interruptible conversation                           │   │
│  │   • Function calling during live session                 │   │
│  └────────────────────────┬─────────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     AGENT ORCHESTRATION LAYER                    │
│                   (Google ADK on Cloud Run)                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              COMPASS Root Agent (Gemini 2.5 Pro)          │   │
│  │   • Conversation state management                        │   │
│  │   • System description intake & clarification            │   │
│  │   • Routes to specialist sub-agents                      │   │
│  └────────┬──────────┬──────────┬──────────┬────────────────┘   │
│           │          │          │          │                     │
│  ┌────────▼──┐ ┌─────▼────┐ ┌──▼───────┐ ┌▼──────────────┐    │
│  │ System     │ │ Control  │ │ Gap      │ │ OSCAL         │    │
│  │ Classifier │ │ Mapper   │ │ Analyzer │ │ Generator     │    │
│  │ Agent      │ │ Agent    │ │ Agent    │ │ Agent         │    │
│  │            │ │          │ │          │ │               │    │
│  │ FIPS 199   │ │ 800-53   │ │ Missing  │ │ SSP/POA&M    │    │
│  │ Impact     │ │ Mapping  │ │ Controls │ │ JSON Output  │    │
│  │ Levels     │ │ + AI     │ │ Remediate│ │              │    │
│  └────────────┘ │ Overlay  │ └──────────┘ └──────────────┘    │
│                  └──────────┘                                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    TOOLS LAYER                            │   │
│  │  • control_lookup()     - Query NIST 800-53 controls     │   │
│  │  • classify_system()    - FIPS 199 categorization        │   │
│  │  • map_data_types()     - PII/PHI/CUI/FTI impact map    │   │
│  │  • gap_analysis()       - Compare baseline vs. stated    │   │
│  │  • generate_oscal()     - Build OSCAL JSON SSP/POA&M    │   │
│  │  • validate_oscal()     - Validate against OSCAL schema  │   │
│  │  • threat_lookup()      - MITRE ATLAS threat mapping     │   │
│  │  • search_controls()    - Semantic search over controls  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      DATA & STORAGE LAYER                        │
│                      (Google Cloud)                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Firestore    │  │  Cloud       │  │  Vertex AI         │    │
│  │  (Sessions,   │  │  Storage     │  │  Vector Search     │    │
│  │   Assessments,│  │  (OSCAL      │  │  (800-53 control   │    │
│  │   System      │  │   outputs,   │  │   embeddings,      │    │
│  │   Profiles)   │  │   diagrams)  │  │   AI overlay       │    │
│  └──────────────┘  └──────────────┘  │   embeddings)      │    │
│                                       └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Hackathon Requirements Mapping

| Requirement | How We Meet It |
|---|---|
| **Gemini model** | Gemini 2.5 Pro via Live API for real-time voice + function calling |
| **Google GenAI SDK or ADK** | ADK (Agent Development Kit) for multi-agent orchestration |
| **Google Cloud service** | Cloud Run (hosting), Firestore (state), Cloud Storage (outputs), Vertex AI Vector Search (RAG) |
| **Live API / Real-time interaction** | Bidirectional audio streaming, interruptible, vision input for diagrams |
| **Hosted on Google Cloud** | Full backend on Cloud Run, data on Firestore + GCS |
| **Multimodal** | Voice in/out + vision (architecture diagram analysis) + structured data (OSCAL JSON) |

### Bonus Points
| Bonus | Plan |
|---|---|
| **Blog/content** | Write a dev.to post: "Building a FedRAMP Voice Agent with Gemini Live API" |
| **Automated deployment** | Terraform + Cloud Build for IaC deployment |
| **GDG membership** | Sign up and link profile |

---

## 4. Conversation Flow Design

### Phase 1: System Intake (Voice)
```
COMPASS: "Welcome. I'm COMPASS, your FedRAMP compliance mapping assistant. 
          Let's start by understanding your system. Can you describe what your 
          system does and what kind of data it processes?"

ARCHITECT: "We're building a customer portal that processes personally 
            identifiable information — names, SSNs, and financial records. 
            It's hosted on AWS GovCloud with a React frontend..."

COMPASS: "Got it. Based on PII including SSNs and financial records, I'm 
          initially classifying this as FIPS 199 Moderate with High 
          confidentiality impact. Before I map controls — do you also 
          handle any Federal Tax Information or protected health data?"

ARCHITECT: "No FTI or PHI."

COMPASS: "Confirmed. Your baseline is FedRAMP Moderate — 325 controls 
          across 18 families. I'm now mapping what you've described to 
          specific control implementations. Do you have an architecture 
          diagram you can share? I can analyze it visually."
```

### Phase 2: Vision Analysis (Multimodal)
```
[Architect uploads/shares architecture diagram]

COMPASS: "I can see your architecture diagram. I'm identifying: a React 
          frontend behind CloudFront, an API Gateway routing to Lambda 
          functions, an RDS PostgreSQL database, and an S3 bucket. 
          
          I notice there's no WAF in front of your CloudFront distribution — 
          that's a gap for SC-7 (Boundary Protection). Also, I don't see 
          explicit encryption at rest indicators on your RDS instance — 
          we'll need to confirm SC-28 (Protection of Information at Rest).
          
          Let me walk through each component and the controls that apply..."
```

### Phase 3: Control Mapping & Gap Analysis (Interactive)
```
COMPASS: "For your API Gateway, I've mapped 12 controls. Let me highlight 
          the critical ones. AC-4, Information Flow Enforcement — how are you 
          controlling data flow between your Lambda functions and RDS?"

ARCHITECT: "We use IAM roles and security groups..."

COMPASS: "Good — that covers network-level AC-4. But FedRAMP Moderate also 
          requires content-based filtering for AC-4. Are you inspecting 
          request/response payloads for sensitive data leakage?"

ARCHITECT: "Not yet."

COMPASS: "I'll flag that as a gap. Recommended remediation: implement an 
          API Gateway request validator with a Lambda authorizer that 
          inspects payloads against a PII pattern library. I'm adding this 
          to your Plan of Action and Milestones. Moving to the next control..."
```

### Phase 4: OSCAL Output Generation
```
COMPASS: "We've mapped 247 of 325 controls to your system description. 
          78 controls need additional information or have identified gaps. 
          
          I've generated three artifacts:
          1. An OSCAL JSON System Security Plan with your implemented controls
          2. An OSCAL POA&M with 23 gap items and remediation timelines
          3. A summary report with your compliance score: 76% implemented, 
             17% partially implemented, 7% not addressed.
          
          I've saved these to your Cloud Storage bucket. Want me to walk 
          through the high-priority gaps?"
```

---

## 5. Technical Implementation

### 5.1 Project Structure

```
compass/
├── README.md                    # Setup + spin-up instructions
├── Dockerfile                   # Cloud Run container
├── terraform/                   # IaC for Google Cloud (bonus)
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── cloudbuild.yaml              # CI/CD pipeline
│
├── backend/
│   ├── app.py                   # FastAPI entrypoint + WebSocket for Live API
│   ├── config.py                # Environment config
│   │
│   ├── agents/                  # ADK Agent definitions
│   │   ├── root_agent.py        # COMPASS orchestrator
│   │   ├── classifier_agent.py  # FIPS 199 system classification
│   │   ├── mapper_agent.py      # 800-53 control mapping
│   │   ├── gap_agent.py         # Gap analysis & remediation
│   │   └── oscal_agent.py       # OSCAL document generation
│   │
│   ├── tools/                   # ADK Tool definitions
│   │   ├── control_lookup.py    # Query NIST 800-53 control database
│   │   ├── classify_system.py   # FIPS 199 impact calculation
│   │   ├── data_type_mapper.py  # PII/PHI/CUI/FTI mapping (from sia_logic_core.py)
│   │   ├── gap_analyzer.py      # Baseline vs. implemented comparison
│   │   ├── oscal_generator.py   # Build OSCAL JSON documents
│   │   ├── oscal_validator.py   # Validate OSCAL schema compliance
│   │   ├── threat_lookup.py     # MITRE ATLAS mapping
│   │   └── vector_search.py     # Semantic search over control corpus
│   │
│   ├── knowledge/               # RAG knowledge base
│   │   ├── nist_800_53_rev5/    # Full control catalog (JSON)
│   │   ├── fedramp_moderate/    # FedRAMP Moderate baseline
│   │   ├── ai_overlay/         # 36 AI-specific controls
│   │   ├── mitre_atlas/        # Threat-to-control mappings
│   │   └── oscal_templates/    # OSCAL SSP/POA&M templates
│   │
│   ├── models/                  # Pydantic data models
│   │   ├── system_profile.py    # System description model
│   │   ├── control_assessment.py # Control mapping result
│   │   ├── gap_finding.py       # Gap analysis finding
│   │   └── oscal_models.py      # OSCAL document models
│   │
│   └── services/                # Google Cloud integrations
│       ├── firestore_service.py # Session & assessment persistence
│       ├── storage_service.py   # OSCAL output storage
│       └── vector_service.py    # Vertex AI Vector Search
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx              # Main app shell
│   │   ├── components/
│   │   │   ├── VoiceSession.tsx  # Gemini Live API WebSocket client
│   │   │   ├── Transcript.tsx    # Real-time conversation display
│   │   │   ├── DiagramUpload.tsx # Architecture diagram upload
│   │   │   ├── ControlPanel.tsx  # Live control mapping display
│   │   │   ├── GapDashboard.tsx  # Gap analysis visualization
│   │   │   └── OSCALViewer.tsx   # OSCAL output preview/download
│   │   └── hooks/
│   │       ├── useLiveAPI.ts     # Gemini Live API hook
│   │       └── useSession.ts     # Session management
│   └── public/
│       └── index.html
│
└── tests/
    ├── test_classifier.py
    ├── test_mapper.py
    ├── test_oscal_generator.py
    └── test_integration.py
```

### 5.2 Core Agent Implementation (ADK)

```python
# backend/agents/root_agent.py
from google.adk import Agent, Tool
from google.adk.agents import SequentialAgent, ParallelAgent

# Sub-agent imports
from .classifier_agent import classifier_agent
from .mapper_agent import mapper_agent
from .gap_agent import gap_agent
from .oscal_agent import oscal_agent

# Tool imports
from tools.control_lookup import control_lookup
from tools.classify_system import classify_system
from tools.data_type_mapper import map_data_types
from tools.gap_analyzer import analyze_gaps
from tools.oscal_generator import generate_oscal
from tools.oscal_validator import validate_oscal
from tools.threat_lookup import lookup_threats
from tools.vector_search import search_controls

compass_agent = Agent(
    model="gemini-2.5-pro",
    name="compass_root",
    description="FedRAMP Compliance Mapping & Policy Assessment Speech System",
    instruction="""You are COMPASS, an expert FedRAMP compliance voice assistant.
    
    Your role is to guide security architects through the FedRAMP authorization 
    process via natural conversation. You:
    
    1. LISTEN to system descriptions and ask targeted clarifying questions
    2. CLASSIFY systems using FIPS 199 (Confidentiality, Integrity, Availability)
    3. MAP described components to applicable NIST SP 800-53 Rev 5 controls
    4. ANALYZE architecture diagrams when provided (using vision)
    5. IDENTIFY gaps between the FedRAMP baseline and stated implementations
    6. GENERATE OSCAL-formatted SSP and POA&M documents
    
    Conversation guidelines:
    - Be conversational but precise. Use plain language, not jargon dumps.
    - After the architect describes something, confirm your understanding.
    - Ask ONE clarifying question at a time — don't overwhelm.
    - When you identify a gap, explain WHY it's a gap and suggest remediation.
    - Support interruptions gracefully — the architect can redirect at any time.
    - When analyzing a diagram, describe what you see before making assessments.
    - Track all findings in the session state for OSCAL generation.
    
    For AI systems, apply the 36-control AI overlay (AI-GOV, AI-DATA, AI-MOD, 
    AI-IO, AI-AUD/IR/PROV, AI-SCRM) on top of the standard 800-53 baseline.
    
    Always ground your control mappings in specific control IDs and enhancement 
    numbers (e.g., "AC-4(4) — Information Flow Enforcement | Content Check").
    """,
    tools=[
        control_lookup,
        classify_system, 
        map_data_types,
        analyze_gaps,
        generate_oscal,
        validate_oscal,
        lookup_threats,
        search_controls,
    ],
    sub_agents=[
        classifier_agent,
        mapper_agent,
        gap_agent,
        oscal_agent,
    ],
)
```

### 5.3 Gemini Live API Integration

```python
# backend/app.py
import asyncio
from fastapi import FastAPI, WebSocket
from google import genai
from google.genai import types

app = FastAPI()

client = genai.Client(
    vertexai=True,
    project="compass-fedramp",
    location="us-central1",
)

LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO", "TEXT"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"  # Professional, clear voice
            )
        )
    ),
    tools=[
        # Function declarations for control lookup, classification, etc.
        types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="classify_system",
                description="Classify a system using FIPS 199 based on data types",
                parameters={
                    "type": "object",
                    "properties": {
                        "data_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Data types processed (PII, PHI, CUI, FTI, Financial)"
                        },
                        "system_description": {
                            "type": "string",
                            "description": "Brief system description"
                        }
                    },
                    "required": ["data_types"]
                }
            ),
            types.FunctionDeclaration(
                name="lookup_controls",
                description="Look up NIST 800-53 controls for a component or requirement",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Component or requirement to map to controls"
                        },
                        "family": {
                            "type": "string",
                            "description": "Optional: specific control family (AC, AU, CM, etc.)"
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.FunctionDeclaration(
                name="analyze_gap",
                description="Analyze a compliance gap for a specific control",
                parameters={
                    "type": "object",
                    "properties": {
                        "control_id": {"type": "string"},
                        "current_implementation": {"type": "string"},
                        "required_implementation": {"type": "string"}
                    },
                    "required": ["control_id", "current_implementation"]
                }
            ),
            types.FunctionDeclaration(
                name="generate_oscal_output",
                description="Generate OSCAL JSON documents from assessment findings",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_type": {
                            "type": "string",
                            "enum": ["ssp", "poam", "assessment_results"]
                        }
                    },
                    "required": ["document_type"]
                }
            ),
        ])
    ],
    system_instruction=types.Content(
        parts=[types.Part(text=COMPASS_SYSTEM_PROMPT)]
    ),
)


@app.websocket("/ws/live")
async def live_session(websocket: WebSocket):
    """Handle bidirectional audio streaming via Gemini Live API."""
    await websocket.accept()
    
    async with client.aio.live.connect(
        model="gemini-2.5-pro",
        config=LIVE_CONFIG,
    ) as session:
        
        async def receive_audio():
            """Receive audio chunks from client and forward to Gemini."""
            while True:
                data = await websocket.receive_bytes()
                await session.send(
                    input=types.LiveClientRealtimeInput(
                        media_chunks=[
                            types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                        ]
                    )
                )
        
        async def send_responses():
            """Receive responses from Gemini and forward to client."""
            async for response in session.receive():
                # Handle audio responses
                if response.data:
                    await websocket.send_bytes(response.data)
                
                # Handle text responses (for transcript)
                if response.text:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": response.text
                    })
                
                # Handle function calls
                if response.tool_call:
                    result = await handle_tool_call(response.tool_call)
                    await session.send(
                        input=types.LiveClientToolResponse(
                            function_responses=[result]
                        )
                    )
        
        await asyncio.gather(receive_audio(), send_responses())
```

### 5.4 Key Tool: FIPS 199 Classifier (Reusing sia_logic_core.py)

```python
# backend/tools/classify_system.py
from google.adk import Tool

# Adapted from existing sia_logic_core.py ImpactEngine
DATA_TYPE_IMPACT_MAP = {
    "PII": {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "PII_SSN": {"confidentiality": "high", "integrity": "high", "availability": "moderate"},
    "PHI": {"confidentiality": "high", "integrity": "high", "availability": "moderate"},
    "CUI": {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "FTI": {"confidentiality": "high", "integrity": "high", "availability": "high"},
    "Financial": {"confidentiality": "moderate", "integrity": "high", "availability": "moderate"},
    "Auth_Credentials": {"confidentiality": "high", "integrity": "high", "availability": "moderate"},
}

IMPACT_RANK = {"low": 1, "moderate": 2, "high": 3}
RANK_TO_IMPACT = {1: "low", 2: "moderate", 3: "high"}

def classify_system_impl(data_types: list[str], system_description: str = "") -> dict:
    """Classify system using FIPS 199 high-water-mark methodology."""
    max_c, max_i, max_a = 1, 1, 1
    
    for dt in data_types:
        dt_upper = dt.upper().replace(" ", "_")
        if dt_upper in DATA_TYPE_IMPACT_MAP:
            impacts = DATA_TYPE_IMPACT_MAP[dt_upper]
            max_c = max(max_c, IMPACT_RANK[impacts["confidentiality"]])
            max_i = max(max_i, IMPACT_RANK[impacts["integrity"]])
            max_a = max(max_a, IMPACT_RANK[impacts["availability"]])
    
    overall = max(max_c, max_i, max_a)
    
    # Map to FedRAMP baseline
    baseline_map = {1: "FedRAMP Low", 2: "FedRAMP Moderate", 3: "FedRAMP High"}
    control_count = {1: 156, 2: 325, 3: 421}
    
    return {
        "fips_199_classification": {
            "confidentiality": RANK_TO_IMPACT[max_c],
            "integrity": RANK_TO_IMPACT[max_i],
            "availability": RANK_TO_IMPACT[max_a],
            "overall": RANK_TO_IMPACT[overall],
        },
        "fedramp_baseline": baseline_map[overall],
        "control_count": control_count[overall],
        "data_types_analyzed": data_types,
    }

classify_system = Tool(
    name="classify_system",
    description="Classify a system using FIPS 199 based on data types processed",
    function=classify_system_impl,
)
```

### 5.5 Key Tool: OSCAL Generator

```python
# backend/tools/oscal_generator.py
import json
import uuid
from datetime import datetime
from google.adk import Tool

def generate_oscal_ssp(system_profile: dict, control_mappings: list[dict]) -> dict:
    """Generate OSCAL-formatted System Security Plan."""
    return {
        "system-security-plan": {
            "uuid": str(uuid.uuid4()),
            "metadata": {
                "title": f"SSP - {system_profile.get('system_name', 'Unnamed System')}",
                "last-modified": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0",
                "oscal-version": "1.1.2",
                "roles": [
                    {"id": "system-owner", "title": "System Owner"},
                    {"id": "authorizing-official", "title": "Authorizing Official"},
                    {"id": "compass-agent", "title": "COMPASS AI Assessment Agent"},
                ],
            },
            "import-profile": {
                "href": "#fedramp-moderate-baseline"
            },
            "system-characteristics": {
                "system-id": system_profile.get("system_id", str(uuid.uuid4())),
                "system-name": system_profile.get("system_name", ""),
                "description": system_profile.get("description", ""),
                "security-sensitivity-level": system_profile.get("fips_199", "moderate"),
                "system-information": {
                    "information-types": [
                        {
                            "title": dt,
                            "confidentiality-impact": {"base": imp["confidentiality"]},
                            "integrity-impact": {"base": imp["integrity"]},
                            "availability-impact": {"base": imp["availability"]},
                        }
                        for dt, imp in system_profile.get("data_types", {}).items()
                    ]
                },
                "security-impact-level": system_profile.get("impact_levels", {}),
                "authorization-boundary": {
                    "description": system_profile.get("boundary_description", "")
                },
            },
            "system-implementation": {
                "components": system_profile.get("components", []),
            },
            "control-implementation": {
                "description": "Control implementations identified by COMPASS voice assessment",
                "implemented-requirements": [
                    {
                        "uuid": str(uuid.uuid4()),
                        "control-id": cm["control_id"],
                        "statements": [
                            {
                                "statement-id": f"{cm['control_id']}_smt",
                                "description": cm.get("implementation_description", ""),
                            }
                        ],
                        "props": [
                            {
                                "name": "implementation-status",
                                "value": cm.get("status", "planned"),
                            }
                        ],
                    }
                    for cm in control_mappings
                ],
            },
        }
    }

def generate_oscal_poam(gaps: list[dict]) -> dict:
    """Generate OSCAL-formatted Plan of Action & Milestones."""
    return {
        "plan-of-action-and-milestones": {
            "uuid": str(uuid.uuid4()),
            "metadata": {
                "title": "COMPASS-Generated POA&M",
                "last-modified": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0",
                "oscal-version": "1.1.2",
            },
            "poam-items": [
                {
                    "uuid": str(uuid.uuid4()),
                    "title": f"Gap: {gap['control_id']} - {gap.get('title', '')}",
                    "description": gap.get("description", ""),
                    "related-observations": [
                        {"description": gap.get("finding", "")}
                    ],
                    "associated-risks": [
                        {
                            "description": gap.get("risk_description", ""),
                            "risk-level": gap.get("risk_level", "moderate"),
                        }
                    ],
                    "remediation": {
                        "description": gap.get("remediation", ""),
                        "scheduled-completion-date": gap.get("target_date", ""),
                    },
                }
                for gap in gaps
            ],
        }
    }
```

---

## 6. Google Cloud Deployment Architecture

### Services Used

| Service | Purpose | Why |
|---|---|---|
| **Cloud Run** | Host backend (FastAPI + ADK agents) | Serverless, scales to zero, easy container deploy |
| **Firestore** | Session state, system profiles, assessment results | Real-time sync, flexible schema for evolving assessments |
| **Cloud Storage** | OSCAL output files, uploaded diagrams | Durable object storage, signed URLs for download |
| **Vertex AI Vector Search** | Semantic search over 800-53 controls + AI overlay | Sub-second retrieval for relevant controls during live conversation |
| **Artifact Registry** | Docker container storage | CI/CD pipeline target |
| **Cloud Build** | CI/CD pipeline | Automated build/deploy on push |
| **Secret Manager** | API keys, config | Secure credential storage |

### Terraform (IaC — Bonus Points)

```hcl
# terraform/main.tf
resource "google_cloud_run_v2_service" "compass" {
  name     = "compass-voice-agent"
  location = "us-central1"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/compass/backend:latest"
      
      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
    }
    
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
}

resource "google_firestore_database" "compass_db" {
  project     = var.project_id
  name        = "compass"
  location_id = "nam5"
  type        = "FIRESTORE_NATIVE"
}

resource "google_storage_bucket" "oscal_outputs" {
  name     = "${var.project_id}-compass-oscal"
  location = "US"
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition { age = 90 }
    action { type = "Delete" }
  }
}
```

---

## 7. Knowledge Base Preparation

### What to Embed in Vertex AI Vector Search

1. **NIST SP 800-53 Rev 5 Complete Catalog** (~1,189 controls + enhancements)
   - Source: [NIST OSCAL GitHub](https://github.com/usnistgov/oscal-content)
   - Each control as a document chunk with: ID, title, description, supplemental guidance, related controls
   
2. **FedRAMP Moderate Baseline** (325 controls)
   - Source: [FedRAMP Automation GitHub](https://github.com/GSA/fedramp-automation)
   - Baseline-specific parameters and additional requirements

3. **AI Control Overlay** (36 controls from your existing work)
   - Source: Your [OpenAI_Overlay.md](OpenAI_Overlay.md) and [Federal_AI_Security_Framework.md](Federal_AI_Security_Framework.md)
   - AI-GOV, AI-DATA, AI-MOD, AI-IO, AI-AUD/IR/PROV, AI-SCRM

4. **MITRE ATLAS Mappings**
   - Source: Your existing threat-to-control mapping table
   - 15 tactics, 66 techniques with control mitigations

5. **Common Implementation Patterns**
   - Source: Your existing framework narratives and technical writeups
   - Real-world implementation language for SSP control descriptions

---

## 8. Development Timeline (4-Week Sprint)

### Week 1: Foundation (Days 1–7)
- [ ] Set up Google Cloud project, enable APIs (Gemini, Vertex AI, Firestore, Cloud Run)
- [ ] Initialize ADK project structure
- [ ] Build knowledge base: ingest 800-53 controls, FedRAMP baseline, AI overlay into Vector Search
- [ ] Implement core tools: `classify_system`, `control_lookup`, `search_controls`
- [ ] Stand up basic Gemini Live API WebSocket connection (audio in/out)
- [ ] **Milestone:** Can have a basic voice conversation with Gemini about compliance

### Week 2: Agent Intelligence (Days 8–14)
- [ ] Implement `classifier_agent` with FIPS 199 logic (port from sia_logic_core.py)
- [ ] Implement `mapper_agent` with RAG-powered control mapping
- [ ] Implement `gap_agent` with baseline comparison logic
- [ ] Wire tools into Live API function calling
- [ ] Add vision capability: architecture diagram upload and analysis
- [ ] **Milestone:** Can classify a system, map controls, and identify gaps via voice

### Week 3: Output & Polish (Days 15–21)
- [ ] Implement `oscal_agent` and OSCAL SSP/POA&M generation
- [ ] Build frontend: VoiceSession, Transcript, ControlPanel, GapDashboard, OSCALViewer
- [ ] Add Firestore session persistence (resume assessments)
- [ ] Cloud Storage integration for OSCAL output download
- [ ] **Milestone:** End-to-end flow working — voice in → OSCAL out

### Week 4: Deploy & Submit (Days 22–28)
- [ ] Write Terraform + Cloud Build deployment pipeline
- [ ] Deploy to Cloud Run, test end-to-end on GCP
- [ ] Record 4-minute demo video
- [ ] Record GCP proof-of-deployment video
- [ ] Create architecture diagram (final version)
- [ ] Write project description and README with spin-up instructions
- [ ] Write blog post (bonus)
- [ ] Sign up for GDG (bonus)
- [ ] **Submit!**

---

## 9. Demo Script (4 minutes)

| Time | Scene | What Happens |
|---|---|---|
| 0:00–0:30 | **Hook** | Show the problem: architect drowning in spreadsheets, 800-53 PDFs, OSCAL templates. "What if you could just _talk_ through your FedRAMP assessment?" |
| 0:30–1:15 | **System Intake** | Live: architect describes system verbally. COMPASS asks clarifying questions, classifies as FedRAMP Moderate. Show real-time transcript + classification panel updating. |
| 1:15–2:00 | **Vision Analysis** | Upload architecture diagram. COMPASS reads it, identifies components, flags missing WAF (SC-7 gap). Show diagram on screen with annotations appearing. |
| 2:00–2:45 | **Interactive Mapping** | COMPASS walks through control families. Architect answers questions. Show control panel populating in real-time — green (implemented), yellow (partial), red (gap). Demonstrate interruption handling. |
| 2:45–3:30 | **OSCAL Output** | COMPASS generates SSP and POA&M. Show OSCAL JSON on screen. Download artifacts. Show compliance score dashboard. |
| 3:30–4:00 | **Close** | Recap: "COMPASS turns weeks of compliance mapping into a single conversation. Built with Gemini 2.5 Pro Live API, ADK, and Google Cloud. Open-source, extensible, and solving a real problem in federal cybersecurity." |

---

## 10. What Makes This Win

1. **Real problem, real users.** FedRAMP authorization is a $2B+ market pain point. Every cloud vendor going through it would use this.

2. **Multimodal mastery.** Voice + vision + structured data output. Not a gimmick — each modality serves the workflow (voice for intake, vision for diagrams, structured for OSCAL).

3. **Technical depth.** Real NIST 800-53 control mapping, real FIPS 199 classification, real OSCAL output. Not a toy demo.

4. **Existing foundation.** You're not starting from zero — sia_logic_core.py, the AI overlay controls, the risk event schema, and the OSCAL patterns are already built.

5. **Live API showcase.** Interruptible, conversational, function-calling-powered — exactly what the "Live Agents" category asks for.

6. **Standing out.** Every other team will build a tutor, translator, or customer support bot. Nobody is building a compliance voice agent. The judges will remember this.

---

## 11. Reusable Assets from Existing Work

| Existing Asset | Reuse In COMPASS |
|---|---|
| `sia_logic_core.py` → ImpactEngine | `classify_system` tool (FIPS 199 logic) |
| `sia_logic_core.py` → ControlAssessor | `gap_analyzer` tool (AC-2, AC-7, RA-5 validation) |
| `risk_event_schema.json` | Session state model for Firestore |
| AI overlay (36 controls) | Knowledge base + `control_lookup` tool |
| MITRE ATLAS mapping table | `threat_lookup` tool |
| BOBBIE → OSCALValidatorTool pattern | `oscal_validator` tool |
| BOBBIE → Pydantic ControlAssessment | `control_assessment.py` data model |
| Framework Narratives (01–07) | RAG corpus for implementation language |
| DATA_TYPE_IMPACT_MAP | `data_type_mapper` tool |
| Secure RAG architecture pattern | COMPASS's own architecture follows it |

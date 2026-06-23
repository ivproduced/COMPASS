# COMPASS — Concept of Operations (CONOPS)

**C**ompliance **M**apping and **P**olicy **A**ssessment **S**peech **S**ystem

| | |
|---|---|
| **Document** | Concept of Operations |
| **System** | COMPASS |
| **Status** | Draft |
| **Audience** | Security architects, ISSOs, assessors, and the development team |

---

## 1. Purpose

This document describes the operational concept for COMPASS: who uses it, what
problem it solves, how it behaves in normal operation, and the boundaries of its
responsibility. It is intended to give a non-implementation-level reader a clear
picture of *how the system is meant to be used* before they dive into the
architecture and code.

For the detailed system design see [`../README.md`](../README.md) and the
architecture diagram in [`architecture.png`](architecture.png).

---

## 2. Problem Statement

Producing a FedRAMP / NIST SP 800-53 Rev 5 compliance package is slow, manual,
and expertise-bound. Architects must:

- mentally map their system design to hundreds of candidate controls,
- classify the system's FIPS 199 impact level,
- identify gaps and remediation effort, and
- translate all of it into machine-readable OSCAL artifacts.

This work is typically done by hand in spreadsheets and documents, is hard to
keep in sync with the live architecture, and demands deep 800-53 expertise.

---

## 3. Operational Goal

COMPASS lets a security architect **describe a system out loud** — and, where
helpful, show an architecture diagram — and receive **real-time** control
mapping, impact classification, gap analysis, and OSCAL output, driven by an
interruptible bidirectional audio session with Gemini.

The objective is to compress hours of manual compliance mapping into a single
conversational session while keeping a human firmly in the loop.

---

## 4. Stakeholders & Users

| Role | Interest in COMPASS |
|---|---|
| **Security Architect / Engineer** | Primary operator — describes the system, reviews mappings, accepts or corrects results. |
| **ISSO / Compliance Lead** | Consumes the generated SSP / POA&M; owns the authorization package. |
| **Assessor (3PAO)** | Uses OSCAL outputs as an assessment starting point. |
| **Development Team** | Operates, maintains, and extends the system. |

---

## 5. Operational Environment

- **Client:** Modern browser with microphone access (React + WebAudio front end).
- **Transport:** PCM 16 kHz bidirectional audio and JSON events over a WebSocket.
- **Backend:** FastAPI on Cloud Run, bridging to the Gemini Live API via
  `google-genai`.
- **Reasoning:** Gemini 2.5 (Live) plus ADK sub-agents for classify / map / gap /
  OSCAL.
- **Data services:** Vertex AI Vector Search (control RAG), Cloud Firestore
  (session state), Cloud Storage (OSCAL outputs).
- **Connectivity:** Requires network access to Google Cloud; not an offline /
  air-gapped tool.

---

## 6. Operational Scenarios

### 6.1 Nominal Session — Voice-Driven Control Mapping

1. The architect opens the COMPASS web app and starts a live session.
2. They describe the system verbally ("a public web app on Cloud Run with a
   Postgres database holding PII…"), optionally uploading an architecture
   diagram for multimodal analysis.
3. COMPASS streams audio to Gemini Live, which invokes ADK sub-agents to:
   - classify FIPS 199 confidentiality / integrity / availability impact,
   - retrieve and map applicable 800-53 Rev 5 controls via RAG,
   - detect gaps and estimate remediation effort.
4. Results are returned conversationally and as structured UI events in real
   time; the architect can **interrupt** at any point to refine or correct.
5. On request, COMPASS generates OSCAL 1.1.2 artifacts (SSP, POA&M, Assessment
   Results) and uploads them to Cloud Storage.

### 6.2 Vision-Assisted Analysis

The architect shares an architecture diagram. Gemini multimodal input analyzes
the diagram to infer components, data flows, and trust boundaries, enriching the
control mapping without the architect having to narrate every detail.

### 6.3 Threat-Informed Mapping (MITRE ATLAS)

For AI/ML systems, COMPASS looks up relevant MITRE ATLAS techniques and maps
them to mitigating 800-53 controls, surfacing AI-specific risk coverage.

### 6.4 Off-Nominal / Degraded Operation

- **Audio or network interruption:** the session degrades gracefully; session
  state is held in Firestore so the conversation can resume.
- **Low-confidence mapping:** COMPASS flags uncertain mappings for human review
  rather than asserting them as final.
- **Service unavailability (Vertex / Firestore / GCS):** the affected capability
  is reported to the user; the system does not silently produce incomplete
  artifacts.

---

## 7. Operational Flow (Summary)

```
Architect (voice + diagram)
        │  PCM 16kHz / JSON events
        ▼
Browser (React + WebAudio)
        ▼
FastAPI (Cloud Run) — /ws/live
        │  google-genai Live API
        ▼
Gemini 2.5 Live  ── function_calls ──▶ ADK sub-agents
                                         ├─ classify (FIPS 199)
                                         ├─ map      (800-53 RAG)
                                         ├─ gap      (gap analysis)
                                         └─ oscal    (OSCAL output)
        │
        ├─ Vertex AI Vector Search   (control RAG)
        ├─ Cloud Firestore           (session state)
        └─ Cloud Storage             (OSCAL outputs)
```

---

## 8. Assumptions & Constraints

- The operator has sufficient context about the system being assessed to answer
  follow-up questions.
- COMPASS is a **decision-support tool**, not an authority — all output requires
  human review before use in an authorization package.
- Requires Google Cloud connectivity and configured ADC; not for air-gapped
  environments.
- Targets NIST SP 800-53 Rev 5 and OSCAL 1.1.2; other frameworks are out of
  scope for this concept.

---

## 9. Out of Scope

- Continuous monitoring / runtime evidence collection.
- Authoritative authorization decisions or sign-off.
- Frameworks beyond NIST 800-53 Rev 5 (e.g., ISO 27001, SOC 2) in this version.

---

## 10. References

- [`../README.md`](../README.md) — system overview and quick start
- [`architecture.png`](architecture.png) — architecture diagram
- [`rules.txt`](rules.txt) — challenge requirements
- NIST SP 800-53 Rev 5, FIPS 199, OSCAL 1.1.2, MITRE ATLAS

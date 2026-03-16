"""
COMPASS FastAPI Application
Entrypoint for the backend service running on Cloud Run.

Endpoints:
  WebSocket /ws/live                      — Gemini Live API bidirectional audio proxy
  POST      /api/chat/{session_id}        — Text chat via Gemini (non-live)
  POST      /api/agent/{session_id}       — ADK agent pipeline (sub-agent delegation)
  GET       /api/sessions                 — List sessions for authenticated user
  POST      /api/sessions                 — Create a new session
  DELETE    /api/sessions/{id}            — Delete a session and all its data
  GET       /api/sessions/{id}            — Get session state + assessment summary
  GET       /api/assessments/{id}         — Get full control mappings + gaps
  GET       /api/oscal/{id}/{type}        — Get signed OSCAL download URL
  POST      /api/diagrams                 — Upload an architecture diagram
  GET       /api/transcript/{session_id}  — Get conversation transcript
  GET       /health                       — Cloud Run health check
  GET       /health/gemini                — Gemini API connectivity check
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

import uvicorn
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

from backend.agents.prompts import COMPASS_SYSTEM_PROMPT
from backend.config import settings
from backend.models.control_assessment import ComplianceScore
from backend.services.firestore_service import firestore_service
from backend.services.storage_service import storage_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Gemini client — supports both Vertex AI and API-key modes
# ------------------------------------------------------------------
def _build_genai_client() -> genai.Client:
    """Create a google-genai client based on config.

    - If ``google_api_key`` is set (and ``gemini_use_vertex`` is False),
      use the public Gemini API.  Good for local dev without GCP creds.
    - Otherwise use Vertex AI (default for Cloud Run with Workload Identity).
    """
    if settings.google_api_key and not settings.gemini_use_vertex:
        logger.info("Gemini client: API-key mode")
        return genai.Client(api_key=settings.google_api_key)

    logger.info(
        "Gemini client: Vertex AI mode (project=%s, location=%s)",
        settings.google_cloud_project,
        settings.google_cloud_location,
    )
    return genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


genai_client = _build_genai_client()

# ------------------------------------------------------------------
# Live API config — built once, reused per session
# ------------------------------------------------------------------
# Tool declarations — used by the sidecar generate_content call.
# gemini-2.5-flash-native-audio-latest only supports bidiGenerateContent (no
# function calling in Live API), so tools are executed via a parallel
# generate_content call after each completed user turn.
TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="classify_system",
        description="Classify a system using FIPS 199 based on data types processed.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "data_types": types.Schema(
                    type="ARRAY",
                    items=types.Schema(type="STRING"),
                    description=(
                        "List of canonical data type tags. Use the most specific tag available. "
                        "PHI subtypes: PHI_CLINICAL (EHR/patient records), PHI_MENTAL_HEALTH, "
                        "PHI_SUBSTANCE_ABUSE, PHI_GENETIC, PHI_BILLING (insurance/billing), PHI_ADMIN. "
                        "PII subtypes: PII, PII_SSN, PII_FINANCIAL, PII_BIOMETRIC, PII_LOCATION. "
                        "Other: FTI, CJIS, CUI, CUI_CONTROLLED, CUI_EXPORT, FINANCIAL, PAYMENT_CARD, "
                        "AUTH_CREDENTIALS, CRYPTOGRAPHIC_KEYS, TRADE_SECRET, PUBLIC, INTERNAL."
                    ),
                ),
                "system_description": types.Schema(
                    type="STRING",
                    description="Optional system description",
                ),
                "confidentiality_override": types.Schema(
                    type="STRING",
                    description=(
                        "Explicit confidentiality impact level stated by the user: 'low', 'moderate', or 'high'. "
                        "Only set if the user has clearly stated a specific confidentiality level. "
                        "Overrides the data-type high-water-mark for this dimension."
                    ),
                ),
                "integrity_override": types.Schema(
                    type="STRING",
                    description=(
                        "Explicit integrity impact level stated by the user: 'low', 'moderate', or 'high'. "
                        "Only set if the user has clearly stated a specific integrity level."
                    ),
                ),
                "availability_override": types.Schema(
                    type="STRING",
                    description=(
                        "Explicit availability impact level stated by the user: 'low', 'moderate', or 'high'. "
                        "Only set if the user has clearly stated a specific availability level. "
                        "Example: if user says 'availability can be moderate', pass 'moderate'."
                    ),
                ),
            },
            required=["data_types"],
        ),
    ),
    types.FunctionDeclaration(
        name="map_data_types",
        description=(
            "Map free-text data type descriptions to canonical tags and C/I/A impact levels. "
            "Pass the most specific phrase possible so the right tag is chosen. "
            "PHI subtypes: 'medical records'→PHI_CLINICAL, 'mental health records'→PHI_MENTAL_HEALTH, "
            "'substance abuse records'→PHI_SUBSTANCE_ABUSE, 'genetic data'→PHI_GENETIC, "
            "'medical billing'→PHI_BILLING, 'health care administration'→PHI_ADMIN. "
            "Other examples: 'electronic health records'→PHI_CLINICAL, 'EHR'→PHI_CLINICAL, "
            "'ssn'→PII_SSN, 'credit card data'→PAYMENT_CARD, 'encryption keys'→CRYPTOGRAPHIC_KEYS, "
            "'criminal justice information'→CJIS, 'federal tax information'→FTI."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "descriptions": types.Schema(
                    type="ARRAY",
                    items=types.Schema(type="STRING"),
                    description="List of specific data type phrases, one per item",
                )
            },
            required=["descriptions"],
        ),
    ),
    types.FunctionDeclaration(
        name="search_controls",
        description="Semantic search over NIST 800-53 controls for a component or requirement.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "query": types.Schema(
                    type="STRING",
                    description="Component or requirement to map to controls",
                ),
                "family_filter": types.Schema(
                    type="STRING",
                    description="Optional: restrict to a control family (AC, SC, AU…)",
                ),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="control_lookup",
        description="Look up a specific NIST 800-53 control by ID.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "control_id": types.Schema(
                    type="STRING",
                    description="Control ID (e.g. AC-4, SC-7(3))",
                ),
                "keyword": types.Schema(
                    type="STRING",
                    description="Keyword to search by title or description",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="gap_analysis",
        description="Analyze a compliance gap for a specific control.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "control_id": types.Schema(type="STRING"),
                "current_implementation": types.Schema(type="STRING"),
                "required_implementation": types.Schema(type="STRING"),
                "component": types.Schema(type="STRING"),
            },
            required=["control_id", "current_implementation"],
        ),
    ),
    types.FunctionDeclaration(
        name="generate_oscal",
        description="Generate OSCAL-formatted SSP or POA&M from session assessment data.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "document_type": types.Schema(
                    type="STRING",
                    enum=["ssp", "poam", "assessment_results"],
                ),
                "system_name": types.Schema(type="STRING"),
                "system_description": types.Schema(type="STRING"),
                "fips_199_level": types.Schema(type="STRING"),
            },
            required=["document_type"],
        ),
    ),
    types.FunctionDeclaration(
        name="threat_lookup",
        description="Query MITRE ATLAS AI/ML threat mappings to find mitigating controls.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "query": types.Schema(type="STRING"),
                "technique_id": types.Schema(type="STRING"),
                "tactic": types.Schema(type="STRING"),
            },
        ),
    ),
]

LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=settings.gemini_voice  # "Kore"
            )
        )
    ),
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
            prefix_padding_ms=20,
            silence_duration_ms=1000,
        ),
    ),
    # NOTE: tools intentionally omitted — native-audio Live API models only
    # support bidiGenerateContent (no function calling). Tools run via sidecar
    # generate_content call in analyze_transcript_for_tools().
    system_instruction=types.Content(
        role="user",
        parts=[types.Part(text=COMPASS_SYSTEM_PROMPT)],
    ),
)


# ------------------------------------------------------------------
# App lifecycle
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "COMPASS backend starting (project=%s, model=%s)",
        settings.google_cloud_project,
        settings.gemini_model,
    )
    # Validate Gemini connectivity at startup
    try:
        await genai_client.aio.models.generate_content(
            model=settings.gemini_model,
            contents="Respond with OK.",
            config=types.GenerateContentConfig(
                max_output_tokens=5,
            ),
        )
        logger.info("Gemini API connected ✓  (model=%s)", settings.gemini_model)
    except Exception as exc:
        logger.error("Gemini API connection FAILED at startup: %s", exc)
        # Don't crash — the app can still serve health checks and REST reads
    yield
    logger.info("COMPASS backend shutting down")


app = FastAPI(
    title="COMPASS Backend",
    description="FedRAMP Compliance Mapping & Policy Assessment Speech System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Tool execution router (called when Gemini invokes a function)
# ------------------------------------------------------------------

def _load_baseline_controls(fedramp_baseline: str) -> list[dict]:
    """Return all controls for the given FedRAMP baseline, enriched with
    title and family from the NIST 800-53 catalog."""
    from backend.tools.gap_analyzer import _load_baseline
    from backend.tools.control_lookup import _load_catalog
    ids = _load_baseline(fedramp_baseline)
    catalog = _load_catalog()
    controls = []
    for ctrl_id in ids:
        cat_entry = catalog.get(ctrl_id.upper())
        if not cat_entry:
            continue  # skip IDs not present in catalog (malformed baseline entries)
        controls.append({
            "control_id": ctrl_id,
            "control_title": cat_entry.get("title", ""),
            "control_family": cat_entry.get("family", ctrl_id.split("-")[0] if "-" in ctrl_id else ""),
            "implementation_status": "not_assessed",
            "implementation_description": "",
        })
    return controls


async def execute_tool(function_name: str, args: dict, session_id: str) -> dict:
    """Dispatch a Gemini function call to the matching Python tool.

    Returns the tool result dict **and** a ``_event`` key with a structured
    WebSocket event that should be forwarded to the client for real-time UI
    updates (classification cards, control-mapped tickers, gap alerts, etc.).
    The caller should pop ``_event`` before sending the result back to Gemini.
    """
    from backend.tools.classify_system import classify_system_impl
    from backend.tools.control_lookup import control_lookup_impl
    from backend.tools.data_type_mapper import map_data_types_impl
    from backend.tools.gap_analyzer import gap_analysis_impl
    from backend.tools.oscal_generator import generate_oscal_impl
    from backend.tools.oscal_validator import validate_oscal_impl
    from backend.tools.threat_lookup import threat_lookup_impl
    from backend.tools.vector_search import search_controls_impl

    try:
        # ---- classify_system ----------------------------------------
        if function_name == "classify_system":
            result = classify_system_impl(**args)
            await firestore_service.set_classification(session_id, result)
            await firestore_service.set_phase(session_id, "classification")
            # Update system profile with data types
            session = await firestore_service.get_session(session_id) or {}
            profile = session.get("systemProfile", {})
            profile["data_types"] = result.get("data_types_matched", args.get("data_types", []))
            if args.get("system_description"):
                profile["description"] = args["system_description"]
            await firestore_service.set_system_profile(session_id, profile)
            # Normalize to the flat shape the frontend Classification interface expects
            fips = result.get("fips_199_classification", {})
            cls_ui = {
                "level": fips.get("overall", "moderate"),
                "confidentiality": fips.get("confidentiality", "low"),
                "integrity": fips.get("integrity", "low"),
                "availability": fips.get("availability", "low"),
                "control_count": result.get("control_count", 0),
                "rationale": result.get("rationale", ""),
                "fedramp_baseline": result.get("fedramp_baseline", ""),
            }
            # Pre-populate the Controls tab with the full FedRAMP baseline for
            # this classification so the UI shows all applicable controls immediately.
            baseline_key = result.get("fedramp_baseline", "moderate")
            baseline_controls = _load_baseline_controls(baseline_key)
            logger.info("Pre-populating %d baseline controls for %s", len(baseline_controls), baseline_key)
            for mapping in baseline_controls:
                await firestore_service.upsert_control_mapping(session_id, mapping)
            await firestore_service.set_phase(session_id, "mapping")
            result["_event"] = {
                "type": "classification",
                "data": {
                    **cls_ui,
                    "baseline_controls": [
                        {"control_id": c["control_id"], "control_title": c["control_title"]}
                        for c in baseline_controls[:20]  # send first 20 to WS for preview
                    ],
                },
            }
            return result

        # ---- search_controls ----------------------------------------
        elif function_name == "search_controls":
            result = search_controls_impl(**args)
            # Persist each returned control as a mapping
            controls = result.get("controls", [])
            for ctrl in controls:
                mapping = {
                    "control_id": ctrl.get("id", ""),
                    "control_title": ctrl.get("title", ""),
                    "control_family": ctrl.get("family", ""),
                    "implementation_status": "not_assessed",
                    "implementation_description": "",
                    "confidence_score": ctrl.get("score", 0.0),
                }
                if mapping["control_id"]:
                    await firestore_service.upsert_control_mapping(session_id, mapping)
            await firestore_service.set_phase(session_id, "mapping")
            result["_event"] = {
                "type": "controls_found",
                "data": {
                    "count": len(controls),
                    "controls": [
                        {"control_id": c.get("id", ""), "control_title": c.get("title", "")}
                        for c in controls[:10]
                    ],
                    "search_method": result.get("search_method", ""),
                },
            }
            return result

        # ---- control_lookup -----------------------------------------
        elif function_name == "control_lookup":
            result = control_lookup_impl(**args)
            controls = result.get("controls", [])
            for ctrl in controls:
                mapping = {
                    "control_id": ctrl.get("id", ""),
                    "control_title": ctrl.get("title", ""),
                    "control_family": ctrl.get("family", ""),
                    "implementation_status": "not_assessed",
                    "implementation_description": "",
                }
                if mapping["control_id"]:
                    await firestore_service.upsert_control_mapping(session_id, mapping)
            result["_event"] = {
                "type": "control_mapped",
                "data": {
                    "count": len(controls),
                    "controls": [
                        {"control_id": c.get("id", ""), "control_title": c.get("title", "")}
                        for c in controls[:5]
                    ],
                },
            }
            return result

        # ---- gap_analysis -------------------------------------------
        elif function_name == "gap_analysis":
            result = gap_analysis_impl(**args)
            ctrl_id = args.get("control_id", "")
            # Update the control mapping with implementation status
            mapping_update = {
                "control_id": ctrl_id,
                "implementation_status": result.get("implementation_status", "not_assessed"),
                "implementation_description": args.get("current_implementation", ""),
            }
            if ctrl_id:
                await firestore_service.upsert_control_mapping(session_id, mapping_update)
            if result.get("is_gap"):
                finding = {
                    "control_id": ctrl_id,
                    "gap_description": result.get("current_implementation", ""),
                    "risk_level": result.get("risk_level", "moderate"),
                    "remediation": result.get("remediation", ""),
                    "estimated_effort": result.get("estimated_effort", "weeks"),
                    "component_refs": [args.get("component", "")] if args.get("component") else [],
                }
                await firestore_service.add_gap_finding(session_id, finding)
            await firestore_service.set_phase(session_id, "gaps")
            result["_event"] = {
                "type": "gap_found" if result.get("is_gap") else "control_assessed",
                "data": result,
            }
            return result

        # ---- generate_oscal -----------------------------------------
        elif function_name == "generate_oscal":
            mappings = await firestore_service.get_control_mappings(session_id)
            gaps = await firestore_service.get_gap_findings(session_id)
            session = await firestore_service.get_session(session_id) or {}
            profile = session.get("systemProfile", {})
            full_args = {
                **args,
                "control_mappings": mappings,
                "gap_findings": gaps,
                "system_name": args.get("system_name") or profile.get("systemName", ""),
                "system_description": args.get("system_description") or profile.get("description", ""),
            }
            result = generate_oscal_impl(**full_args)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            doc_type = args.get("document_type", "ssp")
            gcs_path = storage_service.upload_oscal(session_id, doc_type, result.get("content", {}), ts)
            await firestore_service.save_oscal_output(session_id, doc_type, gcs_path)
            result["gcs_path"] = gcs_path
            await firestore_service.set_phase(session_id, "oscal")
            result["_event"] = {
                "type": "oscal_ready",
                "data": {
                    "document_type": doc_type,
                    "uuid": result.get("uuid"),
                    "gcs_path": gcs_path,
                },
            }
            return result

        # ---- validate_oscal -----------------------------------------
        elif function_name == "validate_oscal":
            result = validate_oscal_impl(**args)
            result["_event"] = {
                "type": "oscal_validated",
                "data": result,
            }
            return result

        # ---- map_data_types -----------------------------------------
        elif function_name == "map_data_types":
            result = map_data_types_impl(**args)
            # Update system profile with discovered data types
            session = await firestore_service.get_session(session_id) or {}
            profile = session.get("systemProfile", {})
            existing_types = set(profile.get("data_types", []))
            existing_types.update(result.get("canonical_tags", []))
            profile["data_types"] = sorted(existing_types)
            await firestore_service.set_system_profile(session_id, profile)
            result["_event"] = {
                "type": "data_types_mapped",
                "data": {
                    "canonical_tags": result.get("canonical_tags", []),
                    "classification": result.get("classification", {}),
                },
            }
            return result

        # ---- threat_lookup ------------------------------------------
        elif function_name == "threat_lookup":
            result = threat_lookup_impl(**args)
            result["_event"] = {
                "type": "threats_found",
                "data": {
                    "count": result.get("count", 0),
                    "techniques": result.get("techniques", [])[:5],
                },
            }
            return result

        else:
            logger.warning("Unknown tool: %s", function_name)
            return {"error": f"Unknown tool: {function_name}"}

    except Exception as exc:
        logger.error("Tool %s failed: %s", function_name, exc, exc_info=True)
        return {"error": str(exc)}


# ------------------------------------------------------------------
# Sidecar tool executor — runs after each user turn via generate_content
# (Live API native-audio models don't support function calling)
# ------------------------------------------------------------------

_PHASE_MAP = {
    "classification": "classification",
    "controls_found": "mapping",
    "control_mapped": "mapping",
    "gap_found": "gaps",
    "control_assessed": "gaps",
    "oscal_ready": "oscal",
}


def _sidecar_allowed_tools(cls: dict | None, num_controls: int) -> list[str]:
    """Return the allowed tool names for the sidecar at the current assessment stage.
    Using mode=ANY forces Gemini to call a function — we restrict the list so it
    only picks tools that are actually appropriate right now.

    Baseline controls are pre-populated automatically on classification, so the
    sidecar jumps straight to gap_analysis once a classification exists.
    """
    if not cls:
        # No classification yet — force classify_system directly.
        # Gemini will extract data types from the conversation and pass them in.
        return ["classify_system"]
    # Classification exists: go straight to gap/OSCAL.
    # search_controls is no longer needed — baseline is pre-loaded on classify.
    return ["gap_analysis", "generate_oscal"]


async def analyze_transcript_for_tools(
    session_id: str,
    websocket: WebSocket,
    user_text: str,
) -> None:
    """After each user turn, call generate_content (gemini-2.5-pro) to decide
    which tools to invoke, push UI events to the client, and inject a context
    note back into the Live session so COMPASS stops re-asking for known info."""
    if len(user_text.strip()) < 20:
        return
    try:
        session = await firestore_service.get_session(session_id) or {}
        transcript = await firestore_service.get_transcript(session_id, limit=15)
        convo_text = "\n".join(
            f"{e.get('speaker', '').upper()}: {e.get('text', '')}"
            for e in transcript
            if e.get("text")
        )

        cls = session.get("classification")
        profile = session.get("systemProfile", {})
        state_parts = []
        if cls:
            state_parts.append(f"Already classified: {cls.get('fedramp_baseline', '')}")
        if profile.get("data_types"):
            state_parts.append(f"Data types mapped: {profile['data_types']}")
        num_controls = len(await firestore_service.get_control_mappings(session_id) or [])
        if num_controls:
            state_parts.append(f"Controls mapped: {num_controls}")
        state_str = "\n".join(state_parts) or "Nothing assessed yet."

        allowed_tools = _sidecar_allowed_tools(cls, num_controls)

        prompt = f"""You are a compliance-assessment orchestrator.

Current session state:
{state_str}

Recent conversation:
{convo_text}

Latest user message: {user_text}

You MUST call one of the available tools to advance the compliance assessment.
Choose the single most appropriate tool based on the conversation above.

IMPORTANT for classify_system: If the user has explicitly stated CIA impact levels
(e.g. "availability can be moderate", "confidentiality is high", "integrity is critical"),
you MUST pass those as confidentiality_override / integrity_override / availability_override.
Include all previously identified data_types from the session state when re-classifying."""

        response = await genai_client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="ANY",
                        allowed_function_names=allowed_tools,
                    )
                ),
            ),
        )

        logger.info("Sidecar allowed_tools=%s, num_controls=%d, has_cls=%s",
                    allowed_tools, num_controls, bool(cls))

        for candidate in response.candidates or []:
            for part in (candidate.content.parts or []) if candidate.content else []:
                if hasattr(part, "function_call") and part.function_call:
                    fn_name = part.function_call.name
                    fn_args = dict(part.function_call.args) if part.function_call.args else {}
                    logger.info("Sidecar tool: %s(%s)", fn_name, list(fn_args.keys()))
                    result = await execute_tool(fn_name, fn_args, session_id)
                    logger.info("Sidecar result keys: %s, is_gap=%s, count=%s",
                                list(result.keys())[:8],
                                result.get("is_gap"),
                                result.get("count"))
                    event = result.pop("_event", None)
                    if event:
                        try:
                            await websocket.send_text(json.dumps(event))
                            if phase := _PHASE_MAP.get(event.get("type", "")):
                                await websocket.send_text(json.dumps({
                                    "type": "phase_change",
                                    "phase": phase,
                                }))
                        except Exception:
                            pass  # WS may already be closed

                    # Context injection removed: send_client_content on a live
                    # session causes concurrent gRPC write conflicts → 1011 crashes.
    except Exception as exc:
        logger.error("Sidecar tool analysis failed: %s", exc)


def _build_context_note(fn_name: str, fn_args: dict, result: dict) -> str:
    """Build a short '[COMPASS CONTEXT UPDATE]' note to feed back into the Live session."""
    try:
        if fn_name == "classify_system":
            cls = result.get("fips_199_classification", {})
            baseline = result.get("fedramp_baseline", "")
            matched = result.get("data_types_matched", fn_args.get("data_types", []))
            return (
                f"[COMPASS CONTEXT UPDATE] System classification complete. "
                f"Data types confirmed: {', '.join(matched)}. "
                f"FIPS 199: C={cls.get('confidentiality','?')} I={cls.get('integrity','?')} "
                f"A={cls.get('availability','?')}. Baseline: {baseline}. "
                f"Do NOT ask about data types, impact level, or FedRAMP baseline again."
            )
        if fn_name == "map_data_types":
            tags = result.get("canonical_tags", [])
            return (
                f"[COMPASS CONTEXT UPDATE] Data types mapped: {', '.join(tags)}. "
                f"Do not ask the user to re-describe their data types."
            )
        if fn_name == "search_controls":
            controls = result.get("controls", [])
            ids = [c.get("id", "") for c in controls[:6] if c.get("id")]
            return (
                f"[COMPASS CONTEXT UPDATE] Control mapping complete. "
                f"Top controls identified: {', '.join(ids)}. "
                f"You may proceed to gap analysis."
            )
        if fn_name == "gap_analysis":
            ctrl = fn_args.get("control_id", "")
            status = result.get("implementation_status", "")
            risk = result.get("risk_level", "")
            return (
                f"[COMPASS CONTEXT UPDATE] Gap analysis for {ctrl}: "
                f"status={status}, risk={risk}. "
                f"{'Gap confirmed — remediation required.' if result.get('is_gap') else 'Control satisfied.'}"
            )
        if fn_name == "generate_oscal":
            doc_type = fn_args.get("document_type", "document")
            return (
                f"[COMPASS CONTEXT UPDATE] OSCAL {doc_type.upper()} generated successfully. "
                f"Assessment complete. You may now summarise findings for the architect."
            )
    except Exception:
        pass
    return ""


@app.websocket("/ws/live")
async def live_session(websocket: WebSocket):
    """
    Bidirectional WebSocket proxy between browser client and Gemini Live API.

    Client → Server messages:
      Binary frames: raw PCM audio (16kHz mono 16-bit)
      JSON frames:   { "type": "diagram", "url": "...", "session_id": "..." }
                     { "type": "control_mapped", ... }
                     { "type": "pause" | "resume" | "end_session" }

    Server → Client messages:
      Binary frames: PCM audio from Gemini
      JSON frames:   { "type": "transcript", "speaker": "compass", "text": "...", "final": bool }
                     { "type": "phase_change", "phase": "..." }
                     { "type": "control_mapped", "data": {...} }
                     { "type": "gap_found", "data": {...} }
                     { "type": "classification", "data": {...} }
                     { "type": "oscal_ready", "data": {...} }
                     { "type": "error", "code": "...", "message": "..." }
    """
    await websocket.accept()
    logger.info("WebSocket accepted")

    session_id: str = ""

    try:
        # First JSON frame must be a session init message
        init_frame = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        init_data = json.loads(init_frame)
        session_id = init_data.get("session_id", "")
        user_id = init_data.get("user_id", "anonymous")

        if not session_id:
            session_id = await firestore_service.create_session(user_id)

        await websocket.send_text(json.dumps({
            "type": "status",
            "connectionStatus": "connected",
            "session_id": session_id,
        }))
        logger.info("Live session started: %s", session_id)

        async with genai_client.aio.live.connect(
            model=settings.gemini_live_model,
            config=LIVE_CONFIG,
        ) as gemini_session:

            # History injection via send_client_content was removed —
            # it causes concurrent gRPC write conflicts → 1011 WS crashes
            # on native-audio models. COMPASS system prompt provides enough
            # context; the sidecar reads Firestore for prior conversation.

            async def receive_from_client():
                """Forward client messages to Gemini."""
                try:
                    while True:
                        msg = await websocket.receive()

                        # Browser sent a close frame
                        if msg.get("type") == "websocket.disconnect":
                            logger.info("receive_from_client: browser sent close frame, code=%s", msg.get("code"))
                            break

                        # Binary = PCM audio chunk
                        if "bytes" in msg:
                            audio_data = msg["bytes"]
                            logger.info("audio chunk from client: %d bytes", len(audio_data))
                            await gemini_session.send_realtime_input(
                                audio=types.Blob(
                                    data=audio_data,
                                    mime_type="audio/pcm;rate=16000",
                                )
                            )

                        # Text = JSON control messages
                        elif "text" in msg:
                            data = json.loads(msg["text"])
                            msg_type = data.get("type")

                            if msg_type == "diagram":
                                # Fetch diagram from GCS and send as vision input
                                gcs_url = data.get("url", "")
                                if gcs_url:
                                    try:
                                        image_bytes = storage_service.get_diagram_bytes(gcs_url)
                                        await gemini_session.send_client_content(
                                            turns=[
                                                types.Content(
                                                    role="user",
                                                    parts=[
                                                        types.Part(
                                                            inline_data=types.Blob(
                                                                data=image_bytes,
                                                                mime_type="image/png",
                                                            )
                                                        ),
                                                        types.Part(
                                                            text="I'm sharing my architecture diagram. Please analyze it and identify components, data flows, and any compliance observations."
                                                        ),
                                                    ],
                                                )
                                            ],
                                            turn_complete=True,
                                        )
                                    except Exception as exc:
                                        logger.error("Diagram load failed: %s", exc)

                            elif msg_type == "end_of_turn":
                                    # Flush Gemini's cached audio buffer so VAD can
                                    # make a final decision and the model responds.
                                    # Per the docs the client can resume sending
                                    # audio at any time after this signal.
                                    logger.info("end_of_turn received — sending audio_stream_end")
                                    await gemini_session.send_realtime_input(audio_stream_end=True)

                            elif msg_type == "end_session":
                                await firestore_service.update_session(session_id, {"status": "completed"})
                                break

                except WebSocketDisconnect:
                    logger.info("Client disconnected (clean): %s", session_id)
                except Exception as exc:
                    logger.error("receive_from_client error: %s", exc)

            async def send_to_client():
                """Forward Gemini responses to client."""
                # Accumulate transcription across streaming chunks.
                # Transcription.finished is always None in the SDK so we cannot
                # rely on it. Instead we accumulate text and flush on turn_complete.
                user_buf: list[str] = []
                compass_buf: list[str] = []
                user_flushed = False   # True once we send user text for this turn
                last_user_text = ""    # saved for sidecar after turn_complete

                try:
                    logger.info("send_to_client: waiting for Gemini responses")
                    while True:  # receive() covers one turn; loop for multi-turn
                      async for response in gemini_session.receive():

                        # PCM audio response
                        sc = response.server_content
                        audio_sent = False
                        if response.data:
                            await websocket.send_bytes(response.data)
                            audio_sent = True

                        # Native-audio models may return audio as inline_data in model_turn parts
                        if sc and sc.model_turn and not audio_sent:
                            for part in (sc.model_turn.parts or []):
                                if part.inline_data and part.inline_data.data:
                                    await websocket.send_bytes(part.inline_data.data)
                                    audio_sent = True

                        if sc:
                            # Stream COMPASS output transcription in real-time.
                            # On the FIRST compass chunk, flush the user buffer so
                            # the user bubble appears ABOVE the compass bubble.
                            if sc.output_transcription and sc.output_transcription.text:
                                if not user_flushed and user_buf:
                                    last_user_text = "".join(user_buf)
                                    user_buf.clear()
                                    user_flushed = True
                                    await websocket.send_text(json.dumps({
                                        "type": "transcript",
                                        "speaker": "user",
                                        "text": last_user_text,
                                        "final": True,
                                    }))
                                    await firestore_service.add_transcript_entry(session_id, {
                                        "speaker": "user",
                                        "text": last_user_text,
                                    })
                                compass_buf.append(sc.output_transcription.text)
                                await websocket.send_text(json.dumps({
                                    "type": "transcript",
                                    "speaker": "compass",
                                    "text": sc.output_transcription.text,
                                    "final": False,
                                }))

                            # Buffer user input transcription. Once flushed,
                            # ignore late/echo chunks from the Live API.
                            if sc.input_transcription and sc.input_transcription.text:
                                if not user_flushed:
                                    user_buf.append(sc.input_transcription.text)

                            # turn_complete fires when Gemini finishes its response.
                            if sc.turn_complete:
                                logger.info("turn_complete: user_flushed=%s, compass_buf=%d chunks",
                                            user_flushed, len(compass_buf))

                                if compass_buf:
                                    full_compass = "".join(compass_buf)
                                    compass_buf.clear()
                                    await websocket.send_text(json.dumps({
                                        "type": "transcript",
                                        "speaker": "compass",
                                        "text": full_compass,
                                        "final": True,
                                    }))
                                    await firestore_service.add_transcript_entry(session_id, {
                                        "speaker": "compass",
                                        "text": full_compass,
                                    })

                                # If user buf wasn't flushed yet (e.g. no compass
                                # response, pure user turn), flush now.
                                if user_buf and not user_flushed:
                                    last_user_text = "".join(user_buf)
                                    user_buf.clear()
                                    await websocket.send_text(json.dumps({
                                        "type": "transcript",
                                        "speaker": "user",
                                        "text": last_user_text,
                                        "final": True,
                                    }))
                                    await firestore_service.add_transcript_entry(session_id, {
                                        "speaker": "user",
                                        "text": last_user_text,
                                    })

                                if last_user_text:
                                    logger.info("Sidecar trigger: user turn complete (%d chars)", len(last_user_text))
                                    asyncio.create_task(
                                        analyze_transcript_for_tools(session_id, websocket, last_user_text)
                                    )

                                # Reset for next turn
                                user_flushed = False
                                last_user_text = ""

                        # Text modality fallback (non-native-audio models)
                        if not sc and response.text:
                            await websocket.send_text(json.dumps({
                                "type": "transcript",
                                "speaker": "compass",
                                "text": response.text,
                                "final": True,
                            }))
                            await firestore_service.add_transcript_entry(session_id, {
                                "speaker": "compass",
                                "text": response.text,
                            })

                except WebSocketDisconnect:
                    logger.info("send_to_client: browser disconnected cleanly")
                    pass
                except Exception as exc:
                    logger.error("send_to_client error: %s", exc)
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "code": "stream_error",
                            "message": str(exc),
                        }))
                    except Exception:
                        pass
                finally:
                    logger.info("send_to_client: loop ended (Gemini session closed or error)")

            # 100ms of silence at 16kHz 16-bit mono = 3200 bytes
            _SILENCE = b"\x00" * 3200

            async def keepalive():
                """Send silent audio every 25s to prevent Gemini idle timeout (60s)."""
                try:
                    while True:
                        await asyncio.sleep(25)
                        await gemini_session.send_realtime_input(
                            audio=types.Blob(
                                data=_SILENCE,
                                mime_type="audio/pcm;rate=16000",
                            )
                        )
                except Exception:
                    pass  # Session closed — exit silently

            await asyncio.gather(receive_from_client(), send_to_client(), keepalive())

    except asyncio.TimeoutError:
        await websocket.send_text(json.dumps({
            "type": "error",
            "code": "init_timeout",
            "message": "No initialization message received within 10 seconds.",
        }))
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected before init: %s", session_id)
    except Exception as exc:
        logger.error("Live session error: %s", exc, exc_info=True)
        try:
            await websocket.send_text(json.dumps({"type": "error", "code": "fatal", "message": str(exc)}))
        except Exception:
            pass
    finally:
        if session_id:
            await firestore_service.update_session(session_id, {"status": "paused"})
        try:
            await websocket.close()
        except Exception:
            pass  # Already closed by the client — suppress ASGI double-close error


# ------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "compass-backend", "version": "1.0.0"}


@app.get("/health/gemini")
async def gemini_health_check():
    """Verify Gemini API is reachable and responding."""
    try:
        response = await genai_client.aio.models.generate_content(
            model=settings.gemini_model,
            contents="Respond with the single word: OK",
            config=types.GenerateContentConfig(max_output_tokens=5),
        )
        text = (response.text or "").strip()
        return {
            "status": "ok",
            "model": settings.gemini_model,
            "mode": "api_key" if (settings.google_api_key and not settings.gemini_use_vertex) else "vertex_ai",
            "response": text,
        }
    except Exception as exc:
        logger.error("Gemini health check failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"Gemini API unreachable: {exc}")


@app.get("/api/sessions")
async def list_sessions(user_id: str = "anonymous"):
    sessions = await firestore_service.list_sessions(user_id)
    # Normalize Firestore doc id → session_id for the frontend
    for s in sessions:
        if "session_id" not in s:
            s["session_id"] = s.pop("id", "")
    return {"sessions": sessions}


@app.post("/api/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(body: dict = {}):
    user_id = body.get("user_id", "anonymous")
    system_name = body.get("system_name", "")
    session_id = await firestore_service.create_session(user_id, system_name)
    return {"session_id": session_id}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await firestore_service.delete_session(session_id)


@app.get("/api/assessments/{session_id}")
async def get_assessment(session_id: str):
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mappings = await firestore_service.get_control_mappings(session_id)
    gaps = await firestore_service.get_gap_findings(session_id)
    oscal_outputs = await firestore_service.get_oscal_outputs(session_id)

    cls_raw = session.get("classification")
    # Normalize to flat UI shape (handle both old nested and new flat formats)
    if cls_raw:
        fips = cls_raw.get("fips_199_classification", {})
        if fips:
            classification_out: dict | None = {
                "level": fips.get("overall", "moderate"),
                "confidentiality": fips.get("confidentiality", "low"),
                "integrity": fips.get("integrity", "low"),
                "availability": fips.get("availability", "low"),
                "control_count": cls_raw.get("control_count", 0),
                "rationale": cls_raw.get("rationale", ""),
                "fedramp_baseline": cls_raw.get("fedramp_baseline", ""),
            }
        else:
            classification_out = cls_raw  # Already normalized
    else:
        classification_out = None

    baseline_count = (classification_out or {}).get("control_count", 325)
    score = ComplianceScore.from_mappings(  # type: ignore[arg-type]
        mappings=[type("M", (), m)() for m in mappings],  # type: ignore
        baseline_total=baseline_count,
    )

    return {
        "sessionId": session_id,
        "systemProfile": session.get("systemProfile", {}),
        "classification": classification_out,
        "conversationPhase": session.get("conversationPhase", "intake"),
        "controlMappings": mappings,
        "gapFindings": gaps,
        "oscalOutputs": oscal_outputs,
        "complianceScore": score.model_dump(),
    }


@app.post("/api/oscal/{session_id}/generate")
async def generate_oscal_endpoint(session_id: str, body: dict = {}):
    """Trigger OSCAL generation for a session on demand (SSP by default)."""
    from backend.tools.oscal_generator import generate_oscal_impl
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    mappings = await firestore_service.get_control_mappings(session_id)
    gaps = await firestore_service.get_gap_findings(session_id)
    profile = session.get("systemProfile", {})
    doc_type = body.get("document_type", "ssp")
    result = generate_oscal_impl(
        document_type=doc_type,
        control_mappings=mappings,
        gap_findings=gaps,
        system_name=profile.get("systemName", ""),
        system_description=profile.get("description", ""),
    )
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    gcs_path = storage_service.upload_oscal(session_id, doc_type, result.get("content", {}), ts)
    await firestore_service.save_oscal_output(session_id, doc_type, gcs_path)
    await firestore_service.set_phase(session_id, "oscal")
    signed_url = storage_service.generate_signed_url(gcs_path, expiry_minutes=60)
    return {"document_type": doc_type, "download_url": signed_url, "gcs_path": gcs_path}


@app.get("/api/oscal/{session_id}/{doc_type}")
async def get_oscal_download_url(session_id: str, doc_type: str):
    outputs = await firestore_service.get_oscal_outputs(session_id)
    matching = [o for o in outputs if o.get("type") == doc_type]
    if not matching:
        raise HTTPException(status_code=404, detail=f"No {doc_type} found for session {session_id}")
    latest = sorted(matching, key=lambda x: x.get("createdAt", ""))[-1]
    gcs_path = latest.get("gcsPath", "")
    if not gcs_path:
        raise HTTPException(status_code=404, detail="GCS path not found")
    signed_url = storage_service.generate_signed_url(gcs_path, expiry_minutes=60)
    return {"download_url": signed_url, "expires_in_minutes": 60}


@app.post("/api/diagrams")
async def upload_diagram(session_id: str, file: UploadFile = File(...)):
    data = await file.read()
    content_type = file.content_type or "image/png"
    gcs_path = storage_service.upload_diagram(
        session_id=session_id,
        filename=file.filename or "diagram.png",
        data=data,
        content_type=content_type,
    )
    return {"url": gcs_path, "filename": file.filename, "analysis_ready": True}


# ------------------------------------------------------------------
# Text Chat — non-live AI interactions via REST
# ------------------------------------------------------------------

@app.post("/api/chat/{session_id}")
async def text_chat(session_id: str, body: dict):
    """
    Send a text message to COMPASS and get an AI response with tool calls
    executed server-side.  Uses the same Gemini model + system prompt as
    the Live API but over a standard generate-content round-trip.

    Request body:
        { "message": "We process PII including SSNs on AWS GovCloud." }

    Response:
        {
          "reply": "Based on …",
          "events": [ { "type": "classification", "data": {…} }, … ]
        }
    """
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = (body.get("message") or "").strip()
    if not user_message:
        raise HTTPException(status_code=422, detail="message is required")

    # Persist user message to transcript
    await firestore_service.add_transcript_entry(session_id, {
        "speaker": "user",
        "text": user_message,
    })

    # Build conversation context from recent transcript
    transcript = await firestore_service.get_transcript(session_id, limit=20)
    history_contents: list[types.Content] = []
    for entry in transcript[:-1]:  # exclude the one we just added
        role = "model" if entry.get("speaker") == "compass" else "user"
        history_contents.append(
            types.Content(role=role, parts=[types.Part(text=entry.get("text", ""))])
        )
    history_contents.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )

    # Call Gemini with tool declarations (same schema as Live API)
    tool_config = types.Tool(
        function_declarations=TOOL_DECLARATIONS
    )
    response = await genai_client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=history_contents,
        config=types.GenerateContentConfig(
            system_instruction=COMPASS_SYSTEM_PROMPT,
            tools=[tool_config],
        ),
    )

    events: list[dict] = []
    reply_parts: list[str] = []

    # Process response — may contain text + function calls
    MAX_TOOL_ROUNDS = 5
    for _round in range(MAX_TOOL_ROUNDS):
        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if part.text:
                    reply_parts.append(part.text)
                if part.function_call:
                    fn_name = part.function_call.name
                    fn_args = dict(part.function_call.args) if part.function_call.args else {}
                    logger.info("Chat tool call: %s(%s)", fn_name, list(fn_args.keys()))
                    result = await execute_tool(fn_name, fn_args, session_id)
                    event = result.pop("_event", None)
                    if event:
                        events.append(event)

                    # Send tool result back to Gemini for follow-up
                    history_contents.append(candidate.content)
                    history_contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        name=fn_name,
                                        response={"result": result},
                                    )
                                )
                            ],
                        )
                    )

        # Check if there are pending function calls that need another round
        has_fn_calls = any(
            part.function_call
            for candidate in (response.candidates or [])
            for part in (candidate.content.parts or [])
        )
        if not has_fn_calls:
            break

        # Continue the conversation with tool results
        response = await genai_client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=history_contents,
            config=types.GenerateContentConfig(
                system_instruction=COMPASS_SYSTEM_PROMPT,
                tools=[tool_config],
            ),
        )

    reply_text = " ".join(reply_parts).strip()
    if reply_text:
        await firestore_service.add_transcript_entry(session_id, {
            "speaker": "compass",
            "text": reply_text,
        })

    # ── Sidecar tool orchestration ──────────────────────────────────────────
    # COMPASS system prompt produces conversational responses; Gemini often
    # reasons about classification without calling the tool.  Run a separate
    # orchestrator call that FORCES a function call (mode=ANY) so assessment
    # data is always written to Firestore after each user turn.
    if len(user_message) >= 20:
        try:
            session_now = await firestore_service.get_session(session_id) or {}
            tx_now = await firestore_service.get_transcript(session_id, limit=15)
            convo_now = "\n".join(
                f"{e.get('speaker', '').upper()}: {e.get('text', '')}"
                for e in tx_now
                if e.get("text")
            )
            cls_now = session_now.get("classification")
            mappings_now = await firestore_service.get_control_mappings(session_id) or []
            state_parts_now: list[str] = []
            if cls_now:
                state_parts_now.append(
                    f"Already classified: {cls_now.get('fedramp_baseline', cls_now.get('level', ''))}"
                )
            if mappings_now:
                state_parts_now.append(f"Controls mapped: {len(mappings_now)}")
            state_str_now = "\n".join(state_parts_now) or "Nothing assessed yet."

            allowed_now = _sidecar_allowed_tools(cls_now, len(mappings_now))

            orch_prompt = (
                "You are a compliance-assessment orchestrator.\n\n"
                f"Current session state:\n{state_str_now}\n\n"
                f"Recent conversation:\n{convo_now}\n\n"
                f"Latest user message: {user_message}\n\n"
                "You MUST call one of the available tools to advance the compliance assessment. "
                "Choose the single most appropriate tool based on the conversation above."
            )
            orch_resp = await genai_client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=orch_prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode="ANY",
                            allowed_function_names=allowed_now,
                        )
                    ),
                ),
            )
            for cand in orch_resp.candidates or []:
                for part in (cand.content.parts or []) if cand.content else []:
                    if hasattr(part, "function_call") and part.function_call:
                        fn = part.function_call.name
                        fa = dict(part.function_call.args) if part.function_call.args else {}
                        logger.info("Text-chat sidecar tool: %s(%s)", fn, list(fa.keys()))
                        tool_result = await execute_tool(fn, fa, session_id)
                        ev = tool_result.pop("_event", None)
                        if ev:
                            events.append(ev)
                            if phase_key := _PHASE_MAP.get(ev.get("type", "")):
                                events.append({"type": "phase_change", "phase": phase_key})
        except Exception as orch_exc:
            logger.error("Text-chat sidecar analysis failed: %s", orch_exc)

    return {"reply": reply_text, "events": events}


# ------------------------------------------------------------------
# Transcript
# ------------------------------------------------------------------

@app.get("/api/transcript/{session_id}")
async def get_transcript(session_id: str, limit: int = 50):
    """Return the conversation transcript for a session."""
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    entries = await firestore_service.get_transcript(session_id, limit=limit)
    return {"session_id": session_id, "entries": entries}


# ------------------------------------------------------------------
# ADK Agent Runner — full agentic endpoint with sub-agent delegation
# ------------------------------------------------------------------
# Lazy-init to avoid import-time failures if ADK is not available
_adk_runner = None
_adk_session_service = None


def _get_adk_runner():
    """Lazy-initialise the ADK Runner + InMemorySessionService."""
    global _adk_runner, _adk_session_service
    if _adk_runner is not None:
        return _adk_runner, _adk_session_service
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from backend.agents.root_agent import root_agent

        _adk_session_service = InMemorySessionService()
        _adk_runner = Runner(
            agent=root_agent,
            app_name="compass",
            session_service=_adk_session_service,
        )
        logger.info("ADK Runner initialised with root_agent (4 sub-agents)")
        return _adk_runner, _adk_session_service
    except Exception as exc:
        logger.error("ADK Runner init failed: %s", exc)
        raise


@app.post("/api/agent/{session_id}")
async def agent_chat(session_id: str, body: dict):
    """
    Send a message through the full ADK agent pipeline.

    This uses the ADK Runner which enables the root_agent to delegate
    to sub-agents (classifier, mapper, gap, oscal) automatically based
    on the conversation phase.  All tools are invoked by the agents
    themselves — no manual dispatch needed.

    Request body:
        { "message": "...", "user_id": "..." }

    Response:
        {
          "reply": "...",
          "agent": "compass_root",
          "events": [ ... ]
        }
    """
    runner, session_service = _get_adk_runner()

    user_message = (body.get("message") or "").strip()
    if not user_message:
        raise HTTPException(status_code=422, detail="message is required")
    user_id = body.get("user_id", "anonymous")

    # Get or create an ADK session mapped to the Firestore session
    from google.genai import types as genai_types

    # Use session_id as the ADK session ID for consistency
    adk_session = await session_service.get_session(
        app_name="compass",
        user_id=user_id,
        session_id=session_id,
    )
    if adk_session is None:
        adk_session = await session_service.create_session(
            app_name="compass",
            user_id=user_id,
            session_id=session_id,
        )

    # Persist user message to Firestore transcript
    await firestore_service.add_transcript_entry(session_id, {
        "speaker": "user",
        "text": user_message,
    })

    # Build the user content
    user_content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    reply_parts: list[str] = []
    events: list[dict] = []
    responding_agent: str = "compass_root"

    # Run the agent — collect all events from the async generator
    async for adk_event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        # Track which agent responded
        if hasattr(adk_event, "author") and adk_event.author:
            responding_agent = adk_event.author

        # Collect text output
        if hasattr(adk_event, "content") and adk_event.content:
            for part in adk_event.content.parts or []:
                if hasattr(part, "text") and part.text:
                    reply_parts.append(part.text)
                # Collect function call events for the frontend
                if hasattr(part, "function_call") and part.function_call:
                    events.append({
                        "type": "tool_call",
                        "tool": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {},
                    })
                if hasattr(part, "function_response") and part.function_response:
                    events.append({
                        "type": "tool_result",
                        "tool": part.function_response.name,
                        "result": part.function_response.response,
                    })

    reply_text = " ".join(reply_parts).strip()
    if reply_text:
        await firestore_service.add_transcript_entry(session_id, {
            "speaker": "compass",
            "text": reply_text,
            "agent": responding_agent,
        })

    return {
        "reply": reply_text,
        "agent": responding_agent,
        "events": events,
    }


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host=settings.host,
        port=settings.port,
        reload=os.getenv("ENV", "production") == "development",
        log_level="info",
    )

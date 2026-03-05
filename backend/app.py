"""
COMPASS FastAPI Application
Entrypoint for the backend service running on Cloud Run.

Endpoints:
  WebSocket /ws/live              — Gemini Live API bidirectional audio proxy
  GET       /api/sessions         — List sessions for authenticated user
  POST      /api/sessions         — Create a new session
  GET       /api/sessions/{id}    — Get session state + assessment summary
  GET       /api/assessments/{id} — Get full control mappings + gaps
  GET       /api/oscal/{id}/{type}— Get signed OSCAL download URL
  POST      /api/diagrams         — Upload an architecture diagram
  GET       /health               — Cloud Run health check
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
    Depends,
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
# Gemini client (module-level singleton)
# ------------------------------------------------------------------
genai_client = genai.Client(
    vertexai=True,
    project=settings.google_cloud_project,
    location=settings.google_cloud_location,
)

# ------------------------------------------------------------------
# Live API config — built once, reused per session
# ------------------------------------------------------------------
LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO", "TEXT"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=settings.gemini_voice  # "Kore"
            )
        )
    ),
    tools=[
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="classify_system",
                    description="Classify a system using FIPS 199 based on data types processed.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "data_types": types.Schema(
                                type="ARRAY",
                                items=types.Schema(type="STRING"),
                                description="List of data types (e.g. PII, PHI, FTI)",
                            ),
                            "system_description": types.Schema(
                                type="STRING",
                                description="Optional system description",
                            ),
                        },
                        required=["data_types"],
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
                    name="map_data_types",
                    description="Map free-text data type descriptions to canonical tags and C/I/A impact levels.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "descriptions": types.Schema(
                                type="ARRAY",
                                items=types.Schema(type="STRING"),
                            )
                        },
                        required=["descriptions"],
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
        )
    ],
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
    logger.info("COMPASS backend starting (project=%s, model=%s)", settings.google_cloud_project, settings.gemini_model)
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

async def execute_tool(function_name: str, args: dict, session_id: str) -> dict:
    """Dispatch a Gemini function call to the matching Python tool."""
    from backend.tools.classify_system import classify_system_impl
    from backend.tools.control_lookup import control_lookup_impl
    from backend.tools.data_type_mapper import map_data_types_impl
    from backend.tools.gap_analyzer import gap_analysis_impl
    from backend.tools.oscal_generator import generate_oscal_impl
    from backend.tools.threat_lookup import threat_lookup_impl
    from backend.tools.vector_search import search_controls_impl

    try:
        if function_name == "classify_system":
            result = classify_system_impl(**args)
            # Persist classification to Firestore
            await firestore_service.set_classification(session_id, result)
            await firestore_service.set_phase(session_id, "classification")
            return result

        elif function_name == "search_controls":
            return search_controls_impl(**args)

        elif function_name == "control_lookup":
            return control_lookup_impl(**args)

        elif function_name == "gap_analysis":
            result = gap_analysis_impl(**args)
            if result.get("is_gap"):
                from backend.models.gap_finding import GapFinding
                finding = {
                    "control_id": args.get("control_id", ""),
                    "gap_description": result.get("current_implementation", ""),
                    "risk_level": result.get("risk_level", "moderate"),
                    "remediation": result.get("remediation", ""),
                    "estimated_effort": result.get("estimated_effort", "weeks"),
                    "component_refs": [args.get("component", "")] if args.get("component") else [],
                }
                await firestore_service.add_gap_finding(session_id, finding)
            return result

        elif function_name == "generate_oscal":
            # Fetch accumulated session data for generation
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
            # Upload to GCS
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            doc_type = args.get("document_type", "ssp")
            gcs_path = storage_service.upload_oscal(session_id, doc_type, result.get("content", {}), ts)
            await firestore_service.save_oscal_output(session_id, doc_type, gcs_path)
            result["gcs_path"] = gcs_path
            return result

        elif function_name == "map_data_types":
            return map_data_types_impl(**args)

        elif function_name == "threat_lookup":
            return threat_lookup_impl(**args)

        else:
            logger.warning("Unknown tool: %s", function_name)
            return {"error": f"Unknown tool: {function_name}"}

    except Exception as exc:
        logger.error("Tool %s failed: %s", function_name, exc, exc_info=True)
        return {"error": str(exc)}


# ------------------------------------------------------------------
# WebSocket: Gemini Live API proxy
# ------------------------------------------------------------------

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
            model=settings.gemini_model,
            config=LIVE_CONFIG,
        ) as gemini_session:

            async def receive_from_client():
                """Forward client messages to Gemini."""
                try:
                    while True:
                        msg = await websocket.receive()

                        # Binary = PCM audio chunk
                        if "bytes" in msg:
                            await gemini_session.send(
                                input=types.LiveClientRealtimeInput(
                                    media_chunks=[
                                        types.Blob(
                                            data=msg["bytes"],
                                            mime_type="audio/pcm;rate=16000",
                                        )
                                    ]
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
                                        await gemini_session.send(
                                            input=types.LiveClientContent(
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
                                                ]
                                            )
                                        )
                                    except Exception as exc:
                                        logger.error("Diagram load failed: %s", exc)

                            elif msg_type == "end_session":
                                await firestore_service.update_session(session_id, {"status": "completed"})
                                break

                except WebSocketDisconnect:
                    logger.info("Client disconnected: %s", session_id)
                except Exception as exc:
                    logger.error("receive_from_client error: %s", exc)

            async def send_to_client():
                """Forward Gemini responses to client."""
                try:
                    async for response in gemini_session.receive():
                        # PCM audio response
                        if response.data:
                            await websocket.send_bytes(response.data)

                        # Text transcript
                        if response.text:
                            await websocket.send_text(json.dumps({
                                "type": "transcript",
                                "speaker": "compass",
                                "text": response.text,
                                "final": True,
                            }))
                            # Persist to Firestore
                            await firestore_service.add_transcript_entry(session_id, {
                                "speaker": "compass",
                                "text": response.text,
                            })

                        # Function call — execute and return result
                        if response.tool_call:
                            for fn_call in response.tool_call.function_calls:
                                fn_name = fn_call.name
                                fn_args = dict(fn_call.args) if fn_call.args else {}
                                logger.info("Tool call: %s(%s)", fn_name, list(fn_args.keys()))

                                result = await execute_tool(fn_name, fn_args, session_id)

                                # Send structured event to client for UI updates
                                if fn_name == "classify_system":
                                    await websocket.send_text(json.dumps({
                                        "type": "classification",
                                        "data": result,
                                    }))
                                elif fn_name == "gap_analysis" and result.get("is_gap"):
                                    await websocket.send_text(json.dumps({
                                        "type": "gap_found",
                                        "data": result,
                                    }))
                                elif fn_name == "generate_oscal":
                                    await websocket.send_text(json.dumps({
                                        "type": "oscal_ready",
                                        "data": {
                                            "document_type": fn_args.get("document_type"),
                                            "uuid": result.get("uuid"),
                                            "gcs_path": result.get("gcs_path"),
                                        },
                                    }))

                                # Return function result to Gemini
                                await gemini_session.send(
                                    input=types.LiveClientToolResponse(
                                        function_responses=[
                                            types.FunctionResponse(
                                                name=fn_name,
                                                id=fn_call.id,
                                                response={"result": result},
                                            )
                                        ]
                                    )
                                )

                except WebSocketDisconnect:
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

            await asyncio.gather(receive_from_client(), send_to_client())

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
        await websocket.close()


# ------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "compass-backend", "version": "1.0.0"}


@app.get("/api/sessions")
async def list_sessions(user_id: str = "anonymous"):
    sessions = await firestore_service.list_sessions(user_id)
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


@app.get("/api/assessments/{session_id}")
async def get_assessment(session_id: str):
    session = await firestore_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mappings = await firestore_service.get_control_mappings(session_id)
    gaps = await firestore_service.get_gap_findings(session_id)
    oscal_outputs = await firestore_service.get_oscal_outputs(session_id)

    baseline_count = session.get("classification", {}).get("control_count", 325) if session.get("classification") else 325
    score = ComplianceScore.from_mappings(  # type: ignore[arg-type]
        mappings=[type("M", (), m)() for m in mappings],  # type: ignore
        baseline_total=baseline_count,
    )

    return {
        "sessionId": session_id,
        "systemProfile": session.get("systemProfile", {}),
        "classification": session.get("classification"),
        "conversationPhase": session.get("conversationPhase", "intake"),
        "controlMappings": mappings,
        "gapFindings": gaps,
        "oscalOutputs": oscal_outputs,
        "complianceScore": score.model_dump(),
    }


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

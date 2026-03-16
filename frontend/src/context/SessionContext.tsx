import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useRef,
  useEffect,
  type ReactNode,
} from "react";
import { api, WS_BASE_URL } from "@/lib/api";

// ─── Types ───────────────────────────────────────────────────────────────────

export type Phase = "intake" | "classification" | "mapping" | "gaps" | "oscal";

export interface TranscriptEntry {
  speaker: "user" | "compass";
  text: string;
  timestamp: string;
  tag?: string;
}

export interface Classification {
  level: string;
  confidentiality: string;
  integrity: string;
  availability: string;
  control_count: number;
  rationale?: string;
}

export interface ControlMapping {
  control_id: string;
  control_title?: string;
  control_family?: string;
  implementation_status: string;
  implementation_description?: string;
}

export interface GapFinding {
  control_id: string;
  gap_description: string;
  risk_level: string;
  remediation?: string;
  estimated_effort?: string;
}

export interface SystemProfile {
  systemName?: string;
  description?: string;
  data_types?: string[];
  hosting?: string;
  components?: string[];
}

export interface OscalDoc {
  type: string;
  gcs_path?: string;
  createdAt?: string;
}

export interface LiveEvent {
  type: string;
  label: string;
  timestamp: Date;
}

export interface ComplianceScore {
  implemented: number;
  partial: number;
  planned: number;
  not_addressed: number;
  total_controls: number;
  mapped_controls: number;
}

// ─── State ───────────────────────────────────────────────────────────────────

interface SessionState {
  sessionId: string | null;
  phase: Phase;
  isConnected: boolean;
  isListening: boolean;
  transcript: TranscriptEntry[];
  systemProfile: SystemProfile | null;
  classification: Classification | null;
  controls: ControlMapping[];
  gaps: GapFinding[];
  oscalDocs: OscalDoc[];
  latestEvent: LiveEvent | null;
  complianceScore: ComplianceScore | null;
  micError: string | null;
}

type Action =
  | { type: "SET_SESSION"; sessionId: string }
  | { type: "SET_CONNECTED"; value: boolean }
  | { type: "SET_LISTENING"; value: boolean }
  | { type: "SET_PHASE"; phase: Phase }
  | { type: "ADD_TRANSCRIPT"; entry: TranscriptEntry }
  | { type: "UPDATE_LAST_TRANSCRIPT"; speaker: "user" | "compass"; text: string }
  | { type: "REPLACE_LAST_TRANSCRIPT"; speaker: "user" | "compass"; text: string }
  | { type: "SET_TRANSCRIPT"; entries: TranscriptEntry[] }
  | { type: "SET_CLASSIFICATION"; data: Classification }
  | { type: "SET_PROFILE"; data: SystemProfile }
  | { type: "UPSERT_CONTROL"; data: ControlMapping }
  | { type: "ADD_GAP"; data: GapFinding }
  | { type: "ADD_OSCAL"; data: OscalDoc }
  | { type: "SET_LATEST_EVENT"; event: LiveEvent }
  | { type: "LOAD_ASSESSMENT"; payload: Partial<SessionState> }
  | { type: "SET_MIC_ERROR"; message: string | null };

const initial: SessionState = {
  sessionId: null,
  phase: "intake",
  isConnected: false,
  isListening: false,
  transcript: [],
  systemProfile: null,
  classification: null,
  controls: [],
  gaps: [],
  oscalDocs: [],
  latestEvent: null,
  complianceScore: null,
  micError: null,
};

function reducer(state: SessionState, action: Action): SessionState {
  switch (action.type) {
    case "SET_SESSION":
      return { ...state, sessionId: action.sessionId };
    case "SET_CONNECTED":
      return { ...state, isConnected: action.value };
    case "SET_LISTENING":
      return { ...state, isListening: action.value };
    case "SET_PHASE":
      return { ...state, phase: action.phase };
    case "ADD_TRANSCRIPT":
      return { ...state, transcript: [...state.transcript, action.entry] };
    case "UPDATE_LAST_TRANSCRIPT": {
      const t = state.transcript;
      if (t.length > 0 && t[t.length - 1].speaker === action.speaker) {
        const updated = [...t];
        updated[updated.length - 1] = { ...updated[updated.length - 1], text: updated[updated.length - 1].text + action.text };
        return { ...state, transcript: updated };
      }
      return {
        ...state,
        transcript: [
          ...t,
          { speaker: action.speaker, text: action.text, timestamp: new Date().toISOString() },
        ],
      };
    }
    case "REPLACE_LAST_TRANSCRIPT": {
      const t = state.transcript;
      if (t.length > 0 && t[t.length - 1].speaker === action.speaker) {
        const updated = [...t];
        updated[updated.length - 1] = { ...updated[updated.length - 1], text: action.text };
        return { ...state, transcript: updated };
      }
      // No matching bubble (poll may have overwritten it) — add as new entry.
      return {
        ...state,
        transcript: [
          ...t,
          { speaker: action.speaker, text: action.text, timestamp: new Date().toISOString() },
        ],
      };
    }
    case "SET_TRANSCRIPT":
      return { ...state, transcript: action.entries };
    case "SET_CLASSIFICATION":
      return { ...state, classification: action.data };
    case "SET_PROFILE":
      return {
        ...state,
        systemProfile: { ...state.systemProfile, ...action.data },
      };
    case "UPSERT_CONTROL": {
      const idx = state.controls.findIndex(
        (c) => c.control_id === action.data.control_id
      );
      const updated =
        idx >= 0
          ? state.controls.map((c, i) =>
              i === idx ? { ...c, ...action.data } : c
            )
          : [...state.controls, action.data];
      return { ...state, controls: updated };
    }
    case "ADD_GAP":
      if (state.gaps.some((g) => g.control_id === action.data.control_id))
        return state;
      return { ...state, gaps: [...state.gaps, action.data] };
    case "ADD_OSCAL":
      return { ...state, oscalDocs: [...state.oscalDocs, action.data] };
    case "SET_LATEST_EVENT":
      return { ...state, latestEvent: action.event };
    case "LOAD_ASSESSMENT":
      return { ...state, ...action.payload };
    case "SET_MIC_ERROR":
      return { ...state, micError: action.message };
    default:
      return state;
  }
}

// ─── Context ─────────────────────────────────────────────────────────────────

interface SessionContextValue extends SessionState {
  connect: (sessionId: string) => void;
  disconnect: () => void;
  startListening: () => Promise<void>;
  stopListening: () => void;
  sendTextMessage: (text: string) => Promise<void>;
  endSession: () => void;
  refreshAssessment: () => Promise<void>;
  clearMicError: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

// ─── PCM helpers ─────────────────────────────────────────────────────────────

function float32ToInt16(buf: Float32Array): Int16Array {
  const out = new Int16Array(buf.length);
  for (let i = 0; i < buf.length; i++) {
    const s = Math.max(-1, Math.min(1, buf[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

function downsampleTo16kHz(input: Float32Array, inputSampleRate: number): Float32Array {
  if (inputSampleRate <= 16000) return input;

  const ratio = inputSampleRate / 16000;
  const outputLength = Math.max(1, Math.round(input.length / ratio));
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.min(input.length, Math.floor((i + 1) * ratio));

    let sum = 0;
    let count = 0;
    for (let j = start; j < end; j++) {
      sum += input[j];
      count += 1;
    }

    output[i] = count > 0 ? sum / count : input[Math.min(start, input.length - 1)] ?? 0;
  }

  return output;
}

// ─── Provider ────────────────────────────────────────────────────────────────

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initial);

  const wsRef = useRef<WebSocket | null>(null);
  const captureCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const playbackCtxRef = useRef<AudioContext | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelayRef = useRef<number>(2000);
  const reconnectAttemptsRef = useRef<number>(0);

  // Keep state in ref so callbacks can access current values without stale closure
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // ── Assessment loader ──────────────────────────────────────────────────────

  const loadAssessment = useCallback(async (sessionId: string, skipTranscript = false) => {
    try {
      const data = await api.getAssessment(sessionId);
      dispatch({
        type: "LOAD_ASSESSMENT",
        payload: {
          phase: (data.conversationPhase as Phase) ?? "intake",
          systemProfile: data.systemProfile ?? null,
          classification: data.classification ?? null,
          controls: data.controlMappings ?? [],
          gaps: data.gapFindings ?? [],
          oscalDocs: data.oscalOutputs ?? [],
          complianceScore: data.complianceScore ?? null,
        },
      });
    } catch {
      // New session — no data yet, that's fine
    }

    if (!skipTranscript) {
      try {
        const tx = await api.getTranscript(sessionId);
        if (tx.entries?.length) {
          dispatch({ type: "SET_TRANSCRIPT", entries: tx.entries });
        }
      } catch {
        // Empty transcript — ok
      }
    }
  }, []);

  const refreshAssessment = useCallback(async () => {
    if (stateRef.current.sessionId) {
      // Skip transcript reload during polling — it overwrites
      // in-progress streaming bubbles from the WebSocket.
      await loadAssessment(stateRef.current.sessionId, true);
    }
  }, [loadAssessment]);

  // ── Server message handler ─────────────────────────────────────────────────

  const handleMessage = useCallback(
    (msg: Record<string, unknown>, sessionId: string) => {
      const type = msg.type as string;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = msg.data as Record<string, any> | undefined;

      switch (type) {
        case "status":
          if (msg.connectionStatus === "connected") {
            dispatch({ type: "SET_CONNECTED", value: true });
            loadAssessment(sessionId);
          }
          break;

        case "transcript": {
          const speaker = msg.speaker === "compass" ? "compass" : "user";
          const text = msg.text as string;
          if (!text) break;

          if (speaker === "compass" && !msg.final) {
            // Stream compass chunks into bubble in real-time.
            dispatch({ type: "UPDATE_LAST_TRANSCRIPT", speaker, text });
          } else if (speaker === "compass" && msg.final) {
            // Replace streamed compass bubble with clean joined text.
            dispatch({ type: "REPLACE_LAST_TRANSCRIPT", speaker, text });
          } else if (speaker === "user" && msg.final) {
            // User text sent as one clean message (before compass streams).
            dispatch({
              type: "ADD_TRANSCRIPT",
              entry: { speaker, text, timestamp: new Date().toISOString() },
            });
          }
          break;
        }

        case "phase_change":
          dispatch({ type: "SET_PHASE", phase: msg.phase as Phase });
          break;

        case "classification": {
          const cls = data as Classification;
          dispatch({ type: "SET_CLASSIFICATION", data: cls });
          // Baseline controls come with the classification event — upsert them
          const baselineControls = (data?.baseline_controls ?? []) as Array<Record<string, unknown>>;
          for (const c of baselineControls) {
            const ctrl = c as ControlMapping;
            if (ctrl?.control_id) dispatch({ type: "UPSERT_CONTROL", data: ctrl });
          }
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `Classified as FedRAMP ${cls?.level ?? ""}`,
              timestamp: new Date(),
            },
          });
          break;
        }

        case "controls_found": {
          // Add each control to state so ControlsTab populates immediately
          const ctrlList = (data?.controls ?? []) as Array<Record<string, unknown>>;
          for (const c of ctrlList) {
            const ctrl = c as import("./SessionContext").ControlMapping;
            if (ctrl?.control_id) dispatch({ type: "UPSERT_CONTROL", data: ctrl });
          }
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `Found ${data?.count ?? 0} applicable controls`,
              timestamp: new Date(),
            },
          });
          break;
        }

        case "control_mapped":
        case "control_assessed": {
          const ctrl = data as ControlMapping;
          if (ctrl?.control_id) dispatch({ type: "UPSERT_CONTROL", data: ctrl });
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `Mapped ${ctrl?.control_id ?? "control"} → ${ctrl?.implementation_status ?? ""}`,
              timestamp: new Date(),
            },
          });
          break;
        }

        case "gap_found": {
          const gap = data as GapFinding;
          if (gap?.control_id) dispatch({ type: "ADD_GAP", data: gap });
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `Gap: ${gap?.control_id ?? ""} (${gap?.risk_level ?? ""})`,
              timestamp: new Date(),
            },
          });
          break;
        }

        case "data_types_mapped": {
          const tags = data?.canonical_tags as string[] | undefined;
          if (tags) {
            dispatch({
              type: "SET_PROFILE",
              data: { data_types: tags },
            });
          }
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `Data types mapped: ${tags?.slice(0, 3).join(", ") ?? ""}`,
              timestamp: new Date(),
            },
          });
          break;
        }

        case "oscal_ready": {
          const doc: OscalDoc = {
            type: data?.document_type ?? "ssp",
            gcs_path: data?.gcs_path,
            createdAt: new Date().toISOString(),
          };
          dispatch({ type: "ADD_OSCAL", data: doc });
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `OSCAL ${doc.type.toUpperCase()} generated`,
              timestamp: new Date(),
            },
          });
          break;
        }

        case "threats_found":
          dispatch({
            type: "SET_LATEST_EVENT",
            event: {
              type,
              label: `${data?.count ?? 0} threat techniques identified`,
              timestamp: new Date(),
            },
          });
          break;

        case "error":
          console.error("[COMPASS WS]", msg.code, msg.message);
          break;
      }
    },
    [loadAssessment]
  );

  // ── PCM audio playback ─────────────────────────────────────────────────────

  const playPCMAudio = useCallback((buffer: ArrayBuffer) => {
    if (
      !playbackCtxRef.current ||
      playbackCtxRef.current.state === "closed"
    ) {
      playbackCtxRef.current = new AudioContext({ sampleRate: 24000 });
      nextPlayTimeRef.current = 0;
    }
    const ctx = playbackCtxRef.current;
    const int16 = new Int16Array(buffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768.0;
    }
    const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
    audioBuffer.copyToChannel(float32, 0);
    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(ctx.destination);
    const now = ctx.currentTime;
    const startAt = Math.max(now, nextPlayTimeRef.current);
    source.start(startAt);
    nextPlayTimeRef.current = startAt + audioBuffer.duration;
  }, []);

  // ── WebSocket connect ──────────────────────────────────────────────────────

  const connect = useCallback(
    (sessionId: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(`${WS_BASE_URL}/ws/live`);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ session_id: sessionId, user_id: "anonymous" }));
      };

      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          playPCMAudio(event.data);
          return;
        }
        try {
          const msg = JSON.parse(event.data as string);
          handleMessage(msg, sessionId);
        } catch {
          // Not JSON — ignore
        }
      };

      ws.onclose = () => {
        dispatch({ type: "SET_CONNECTED", value: false });
        dispatch({ type: "SET_LISTENING", value: false });
        reconnectAttemptsRef.current += 1;
        // Stop reconnecting after 5 failures — voice is broken, text chat still works
        if (reconnectAttemptsRef.current > 5) return;
        // Auto-reconnect with capped exponential backoff
        const delay = reconnectDelayRef.current;
        reconnectTimerRef.current = setTimeout(() => {
          const sid = stateRef.current.sessionId;
          if (sid) {
            reconnectDelayRef.current = Math.min(delay * 2, 30000);
            connect(sid);
          }
        }, delay);
      };

      ws.onerror = () => {
        dispatch({ type: "SET_CONNECTED", value: false });
      };

      dispatch({ type: "SET_SESSION", sessionId });
      reconnectDelayRef.current = 2000; // reset backoff on explicit connect
    reconnectAttemptsRef.current = 0; // reset failure counter on explicit connect
    },
    [handleMessage, playPCMAudio]
  );

  // ── Audio capture ──────────────────────────────────────────────────────────

  const stopListening = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    captureCtxRef.current?.close();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    processorRef.current = null;
    sourceRef.current = null;
    captureCtxRef.current = null;
    streamRef.current = null;
    dispatch({ type: "SET_LISTENING", value: false });
    // Signal to Gemini that the user's turn is complete
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "end_of_turn" }));
    }
  }, []);

  const startListening = useCallback(async () => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true },
      });
      streamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: 16000 });
      captureCtxRef.current = audioCtx;
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      // eslint-disable-next-line @typescript-eslint/no-deprecated
      const processor = audioCtx.createScriptProcessor(2048, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const liveWs = wsRef.current;
        if (!liveWs || liveWs.readyState !== WebSocket.OPEN) return;
        const pcm = downsampleTo16kHz(
          e.inputBuffer.getChannelData(0),
          e.inputBuffer.sampleRate,
        );
        const int16 = float32ToInt16(pcm);
        liveWs.send(int16.buffer);
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);

      dispatch({ type: "SET_LISTENING", value: true });
    } catch (err) {
      console.error("Microphone access denied:", err);
      const msg =
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Microphone permission denied. Please allow mic access in your browser and try again."
          : "Could not access microphone. Check your browser settings.";
      dispatch({ type: "SET_MIC_ERROR", message: msg });
    }
  }, []);

  // ── Text chat (REST fallback) ──────────────────────────────────────────────

  const sendTextMessage = useCallback(
    async (text: string) => {
      const sessionId = stateRef.current.sessionId;
      if (!sessionId) return;

      dispatch({
        type: "ADD_TRANSCRIPT",
        entry: {
          speaker: "user",
          text,
          timestamp: new Date().toISOString(),
        },
      });

      try {
        const res = await api.chat(sessionId, text);
        if (res.reply) {
          dispatch({
            type: "ADD_TRANSCRIPT",
            entry: {
              speaker: "compass",
              text: res.reply,
              timestamp: new Date().toISOString(),
            },
          });
        }
        // Dispatch tool-call events returned by the REST sidecar
        for (const event of res.events ?? []) {
          handleMessage(event as Record<string, unknown>, sessionId);
        }
        await loadAssessment(sessionId);
      } catch (err) {
        console.error("Chat failed:", err);
      }
    },
    [loadAssessment]
  );

  // ── Disconnect ─────────────────────────────────────────────────────────────

  const disconnect = useCallback(() => {
    // Cancel any pending reconnect
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    reconnectDelayRef.current = 2000;
    stopListening();
    wsRef.current?.close();
    wsRef.current = null;
    playbackCtxRef.current?.close();
    playbackCtxRef.current = null;
    dispatch({ type: "SET_CONNECTED", value: false });
  }, [stopListening]);

  const endSession = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_session" }));
    }
    disconnect();
  }, [disconnect]);

  const clearMicError = useCallback(() => {
    dispatch({ type: "SET_MIC_ERROR", message: null });
  }, []);

  useEffect(() => () => { disconnect(); }, [disconnect]);

  // Poll Firestore for panel updates every 6 s while a session is active.
  // This is the safety net for the voice path: the sidecar runs async so
  // WebSocket events may arrive slightly after the panel data is written.
  useEffect(() => {
    const sid = state.sessionId;
    if (!sid) return;
    const id = setInterval(() => { refreshAssessment(); }, 6000);
    return () => clearInterval(id);
  }, [state.sessionId, refreshAssessment]);

  return (
    <SessionContext.Provider
      value={{
        ...state,
        connect,
        disconnect,
        startListening,
        stopListening,
        sendTextMessage,
        endSession,
        refreshAssessment,
        clearMicError,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within <SessionProvider>");
  return ctx;
}

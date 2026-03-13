const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
export const WS_BASE_URL = (import.meta.env.VITE_WS_BASE_URL ?? BASE_URL).replace(/^http/, "ws");

// ─── Types ────────────────────────────────────────────────────────────────────

export interface SessionSummary {
  session_id: string;
  systemProfile?: { systemName?: string };
  classification?: { level?: string; control_count?: number };
  conversationPhase?: string;
  controlMappings?: unknown[];
  updatedAt?: string;
  createdAt?: string;
  status?: string;
}

export interface AssessmentData {
  sessionId: string;
  systemProfile?: Record<string, unknown>;
  classification?: Record<string, unknown>;
  conversationPhase?: string;
  controlMappings?: unknown[];
  gapFindings?: unknown[];
  oscalOutputs?: unknown[];
  complianceScore?: Record<string, unknown>;
}

export interface TranscriptEntry {
  speaker: "user" | "compass";
  text: string;
  timestamp: string;
}

// ─── HTTP helper ─────────────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ─── API client ───────────────────────────────────────────────────────────────

export const api = {
  // Sessions
  getSessions: (userId = "anonymous") =>
    request<{ sessions: SessionSummary[] }>(`/api/sessions?user_id=${userId}`),
  getSession: (id: string) =>
    request<SessionSummary>(`/api/sessions/${id}`),
  createSession: (systemName?: string, userId = "anonymous") =>
    request<{ session_id: string }>("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ system_name: systemName ?? "", user_id: userId }),
    }),

  // Assessment (controls + gaps + classification + OSCAL)
  getAssessment: (id: string) =>
    request<AssessmentData>(`/api/assessments/${id}`),

  // Transcript
  getTranscript: (id: string, limit = 100) =>
    request<{ entries: TranscriptEntry[] }>(`/api/transcript/${id}?limit=${limit}`),

  // OSCAL download URL
  getOscalUrl: (id: string, type: string) =>
    request<{ download_url: string; expires_in_minutes: number }>(
      `/api/oscal/${id}/${type}`
    ),

  // Diagram upload
  uploadDiagram: (sessionId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE_URL}/api/diagrams?session_id=${sessionId}`, {
      method: "POST",
      body: form,
    }).then((r) => r.json()) as Promise<{ url: string; analysis_ready: boolean }>;
  },

  // Text chat (REST fallback — no audio required)
  chat: (sessionId: string, message: string) =>
    request<{ response: string; tool_calls: unknown[] }>(
      `/api/chat/${sessionId}`,
      { method: "POST", body: JSON.stringify({ message }) }
    ),

  // Health
  health: () => request<{ status: string }>("/health"),
};

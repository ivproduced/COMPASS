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

export interface AssessmentClassification {
  level: string;
  confidentiality: string;
  integrity: string;
  availability: string;
  control_count: number;
  rationale?: string;
}

export interface AssessmentControl {
  control_id: string;
  control_title?: string;
  control_family?: string;
  implementation_status: string;
  implementation_description?: string;
}

export interface AssessmentGap {
  control_id: string;
  gap_description: string;
  risk_level: string;
  remediation?: string;
  estimated_effort?: string;
}

export interface AssessmentOscalDoc {
  type: string;
  gcs_path?: string;
  createdAt?: string;
}

export interface AssessmentComplianceScore {
  implemented: number;
  partial: number;
  planned: number;
  not_addressed: number;
  total_controls: number;
  mapped_controls: number;
}

export interface AssessmentData {
  sessionId: string;
  systemProfile?: Record<string, unknown>;
  classification?: AssessmentClassification;
  conversationPhase?: string;
  controlMappings?: AssessmentControl[];
  gapFindings?: AssessmentGap[];
  oscalOutputs?: AssessmentOscalDoc[];
  complianceScore?: AssessmentComplianceScore;
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
  deleteSession: (id: string) =>
    request<void>(`/api/sessions/${id}`, { method: "DELETE" }),

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

  // Generate OSCAL on demand
  generateOscal: (id: string, documentType = "ssp") =>
    request<{ document_type: string; download_url: string; gcs_path: string }>(
      `/api/oscal/${id}/generate`,
      { method: "POST", body: JSON.stringify({ document_type: documentType }) }
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
    request<{ reply: string; events: Array<{ type: string; data: unknown }> }>(
      `/api/chat/${sessionId}`,
      { method: "POST", body: JSON.stringify({ message }) }
    ),

  // Health
  health: () => request<{ status: string }>("/health"),
};

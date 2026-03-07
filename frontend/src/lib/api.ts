const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

// Session endpoints (scaffold)
export const api = {
  getSessions: () => request("/sessions"),
  getSession: (id: string) => request(`/sessions/${id}`),
  createSession: (data: unknown) =>
    request("/sessions", { method: "POST", body: JSON.stringify(data) }),
  getReport: (sessionId: string) => request(`/sessions/${sessionId}/report`),
};

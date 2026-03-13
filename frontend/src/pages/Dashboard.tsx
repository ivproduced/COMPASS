import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopNav from "@/components/TopNav";
import { Button } from "@/components/ui/button";
import { api, type SessionSummary } from "@/lib/api";

const PHASE_COLOR: Record<string, string> = {
  intake: "bg-gray-500",
  classification: "bg-blue-500",
  mapping: "bg-amber-500",
  gaps: "bg-orange-500",
  oscal: "bg-green-500",
};

function timeAgo(iso?: string) {
  if (!iso) return "—";
  const secs = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
  return `${Math.round(secs / 86400)}d ago`;
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    api
      .getSessions()
      .then((r) => setSessions(r.sessions ?? []))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  const handleNewSession = async () => {
    setCreating(true);
    try {
      const { session_id } = await api.createSession();
      navigate(`/session/${session_id}`);
    } catch {
      setCreating(false);
    }
  };

  const totalMapped = sessions.reduce(
    (n, s) => n + (s.classification?.control_count ?? 0),
    0
  );

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <TopNav pageTitle="Dashboard" />

      <main className="flex-1 p-6 space-y-8 max-w-6xl mx-auto w-full">
        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { value: loading ? "…" : String(sessions.length), label: "Total Sessions" },
            { value: loading ? "…" : String(totalMapped), label: "Total Controls" },
            {
              value: loading ? "…" : String(
                sessions.filter((s) => s.conversationPhase === "oscal").length
              ),
              label: "Completed",
            },
          ].map((s) => (
            <div key={s.label} className="bg-card border border-border rounded-lg p-6">
              <div className="font-bold text-[36px] leading-tight text-foreground">
                {s.value}
              </div>
              <div className="text-sm text-[#64748B] mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg text-foreground">Recent Sessions</h2>
          <Button
            onClick={handleNewSession}
            disabled={creating}
            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md font-medium"
          >
            {creating ? "Creating…" : "+ New Session"}
          </Button>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="grid grid-cols-[40px_1fr_100px_160px_120px] px-4 h-10 items-center border-b border-border text-xs font-medium text-muted-foreground uppercase tracking-wider">
            <span />
            <span>System Name</span>
            <span>Phase</span>
            <span>Controls</span>
            <span>Last Active</span>
          </div>

          {loading ? (
            <div className="px-4 py-6 text-sm text-muted-foreground">Loading…</div>
          ) : sessions.length === 0 ? (
            <div className="px-4 py-6 text-sm text-muted-foreground italic">
              No sessions yet. Click "+ New Session" to start.
            </div>
          ) : (
            sessions.map((s) => {
              const phase = s.conversationPhase ?? "intake";
              const color = PHASE_COLOR[phase] ?? "bg-gray-500";
              const name =
                s.systemProfile?.systemName || s.session_id.slice(0, 8) + "…";
              const level = s.classification?.level ?? "—";
              const mapped = s.classification?.control_count ?? 0;
              return (
                <div
                  key={s.session_id}
                  onClick={() => navigate(`/session/${s.session_id}`)}
                  className="grid grid-cols-[40px_1fr_100px_160px_120px] px-4 h-14 items-center border-b border-border last:border-b-0 cursor-pointer hover:bg-accent/40 transition-colors"
                >
                  <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
                  <span className="text-sm text-foreground">{name}</span>
                  <span className="text-sm text-muted-foreground capitalize">{level}</span>
                  <span className="text-sm text-muted-foreground">
                    {mapped > 0 ? `${mapped} controls` : "—"}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {timeAgo(s.updatedAt ?? s.createdAt)}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

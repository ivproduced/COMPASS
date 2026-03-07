import { useNavigate } from "react-router-dom";
import TopNav from "@/components/TopNav";
import { Button } from "@/components/ui/button";

const stats = [
  { value: "5", label: "Total Sessions" },
  { value: "1,247", label: "Controls Mapped" },
  { value: "34", label: "Open Gaps" },
];

const sessions = [
  { color: "bg-green-500", name: "Customer Portal", baseline: "Moderate", progress: "247 / 325 controls", lastActive: "2 hours ago" },
  { color: "bg-amber-500", name: "Data Analytics Platform", baseline: "High", progress: "89 / 421 controls", lastActive: "1 day ago" },
  { color: "bg-gray-500", name: "Internal Admin Tool", baseline: "Low", progress: "0 / 156 controls", lastActive: "3 days ago" },
];

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <TopNav pageTitle="Dashboard" />

      <main className="flex-1 p-6 space-y-8 max-w-6xl mx-auto w-full">
        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          {stats.map((s) => (
            <div key={s.label} className="bg-card border border-border rounded-lg p-6">
              <div className="font-bold text-[36px] leading-tight text-foreground">{s.value}</div>
              <div className="text-sm text-[#64748B] mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Section header */}
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg text-foreground">Recent Sessions</h2>
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md font-medium">
            + New Session
          </Button>
        </div>

        {/* Session table */}
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="grid grid-cols-[40px_1fr_100px_160px_120px] px-4 h-10 items-center border-b border-border text-xs font-medium text-muted-foreground uppercase tracking-wider">
            <span />
            <span>System Name</span>
            <span>Baseline</span>
            <span>Progress</span>
            <span>Last Active</span>
          </div>

          {sessions.map((s, i) => (
            <div
              key={i}
              onClick={() => navigate("/session/demo-session-1")}
              className="grid grid-cols-[40px_1fr_100px_160px_120px] px-4 h-14 items-center border-b border-border last:border-b-0 cursor-pointer hover:bg-accent/40 transition-colors"
            >
              <span className={`w-2.5 h-2.5 rounded-full ${s.color}`} />
              <span className="text-sm text-foreground">{s.name}</span>
              <span className="text-sm text-muted-foreground">{s.baseline}</span>
              <span className="text-sm text-muted-foreground">{s.progress}</span>
              <span className="text-sm text-muted-foreground">{s.lastActive}</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

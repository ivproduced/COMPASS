import { useSession } from "@/context/SessionContext";

const RISK_CONFIG: Record<string, { emoji: string; bg: string; label: string }> = {
  critical: { emoji: "🔴", bg: "#EF4444", label: "CRITICAL" },
  high:     { emoji: "🟠", bg: "#F97316", label: "HIGH" },
  moderate: { emoji: "🟡", bg: "#F59E0B", label: "MODERATE" },
  low:      { emoji: "🟢", bg: "#22C55E", label: "LOW" },
};

const BORDER: Record<string, string> = {
  critical: "#EF4444",
  high: "#F97316",
  moderate: "#F59E0B",
  low: "#22C55E",
};

const GapsTab = () => {
  const { gaps } = useSession();

  if (gaps.length === 0) {
    return (
      <div className="flex items-center justify-center h-32">
        <p className="text-sm text-muted-foreground italic text-center">
          Gap findings will appear as COMPASS analyses your controls.
        </p>
      </div>
    );
  }

  const counts = { critical: 0, high: 0, moderate: 0, low: 0 };
  for (const g of gaps) {
    const k = g.risk_level?.toLowerCase() as keyof typeof counts;
    if (k in counts) counts[k]++;
  }

  const sorted = [...gaps].sort((a, b) => {
    const order = ["critical", "high", "moderate", "low"];
    return (
      order.indexOf(a.risk_level?.toLowerCase()) -
      order.indexOf(b.risk_level?.toLowerCase())
    );
  });

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-[15px] font-semibold text-foreground">Gap Analysis</h3>
        <p className="text-[13px] text-[#64748B] mt-1">{gaps.length} gap{gaps.length !== 1 ? "s" : ""} found</p>
      </div>

      <div className="flex gap-2">
        {(["critical", "high", "moderate", "low"] as const).map((k) => {
          const cfg = RISK_CONFIG[k];
          return (
            <div
              key={k}
              className="flex-1 flex flex-col items-center rounded-lg px-2 py-3"
              style={{ backgroundColor: cfg.bg }}
            >
              <span className="text-[20px] font-bold text-white leading-none">{counts[k]}</span>
              <span className="text-[10px] font-medium uppercase text-white mt-1 tracking-wide">
                {cfg.emoji} {cfg.label}
              </span>
            </div>
          );
        })}
      </div>

      <div className="space-y-3">
        {sorted.map((gap) => {
          const lvl = gap.risk_level?.toLowerCase();
          const borderColor = BORDER[lvl] ?? "#64748B";
          const cfg = RISK_CONFIG[lvl] ?? { emoji: "⚪", label: lvl?.toUpperCase() };
          return (
            <div
              key={gap.control_id}
              className="bg-background border rounded-lg p-4 space-y-2"
              style={{ borderLeft: `3px solid ${borderColor}` }}
            >
              <div className="flex items-center gap-2">
                <span className="font-mono text-[13px] font-bold text-foreground">
                  {gap.control_id}
                </span>
                <span
                  className="text-[11px] font-bold uppercase px-1.5 py-0.5 rounded"
                  style={{ color: borderColor }}
                >
                  {cfg.emoji} {cfg.label}
                </span>
              </div>
              <p className="text-[13px] text-foreground leading-relaxed">
                {gap.gap_description}
              </p>
              {gap.remediation && (
                <div className="bg-card rounded-md p-2">
                  <p className="text-[12px] font-semibold text-muted-foreground mb-1">Remediation</p>
                  <p className="text-[12px] text-foreground">{gap.remediation}</p>
                </div>
              )}
              {gap.estimated_effort && (
                <p className="text-[12px] text-muted-foreground">
                  Effort: <span className="font-medium text-foreground">{gap.estimated_effort}</span>
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GapsTab;

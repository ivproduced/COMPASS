import { useSession } from "@/context/SessionContext";

const IMPACT: Record<string, { color: string; pct: number }> = {
  HIGH: { color: "#EF4444", pct: 80 },
  MODERATE: { color: "#F59E0B", pct: 60 },
  LOW: { color: "#22C55E", pct: 40 },
};

const LEVEL_COLOR: Record<string, string> = {
  HIGH: "#EF4444",
  MODERATE: "#F59E0B",
  LOW: "#22C55E",
};

const ClassifyTab = () => {
  const { classification } = useSession();

  if (!classification) {
    return (
      <div className="flex items-center justify-center h-32">
        <p className="text-sm text-muted-foreground italic text-center">
          Classification will appear once COMPASS processes your system
          description.
        </p>
      </div>
    );
  }

  const {
    level,
    confidentiality,
    integrity,
    availability,
    control_count,
    rationale,
  } = classification;
  const lvl = (level ?? "").toUpperCase();
  const levelColor = LEVEL_COLOR[lvl] ?? "#64748B";

  const impactLevels = [
    { label: "Confidentiality", level: (confidentiality ?? "").toUpperCase() },
    { label: "Integrity", level: (integrity ?? "").toUpperCase() },
    { label: "Availability", level: (availability ?? "").toUpperCase() },
  ];

  return (
    <>
      <div className="flex flex-col items-center gap-2">
        <span
          className="text-white font-bold text-sm px-4 py-1.5 rounded-lg"
          style={{ backgroundColor: levelColor }}
        >
          {lvl || "—"}
        </span>
        <span className="text-[13px] text-muted-foreground">
          FedRAMP {level} · {control_count ?? "—"} Controls
        </span>
      </div>

      <div className="space-y-1.5">
        <h4 className="text-[13px] font-semibold text-foreground">Impact Levels</h4>
        <div className="space-y-3">
          {impactLevels.map((item) => {
            const cfg = IMPACT[item.level] ?? { color: "#64748B", pct: 30 };
            return (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between text-[12px]">
                  <span className="text-muted-foreground">{item.label}</span>
                  <span className="font-bold" style={{ color: cfg.color }}>
                    {item.level || "—"}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-background">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${cfg.pct}%`, backgroundColor: cfg.color }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {rationale && (
        <div className="space-y-1.5">
          <h4 className="text-[13px] font-semibold text-foreground">Rationale</h4>
          <p className="text-[13px] italic text-muted-foreground leading-relaxed">
            {rationale}
          </p>
        </div>
      )}
    </>
  );
};

export default ClassifyTab;

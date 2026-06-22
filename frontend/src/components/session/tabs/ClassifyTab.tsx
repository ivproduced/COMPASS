import { useSession } from "@/context/SessionContext";

const IMPACT: Record<string, { color: string; pct: number }> = {
  HIGH: { color: "#b50909", pct: 80 },
  MODERATE: { color: "#936f38", pct: 60 },
  LOW: { color: "#1a7f37", pct: 40 },
};

const LEVEL_COLOR: Record<string, string> = {
  HIGH: "#b50909",
  MODERATE: "#936f38",
  LOW: "#1a7f37",
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
  const levelColor = LEVEL_COLOR[lvl] ?? "#71767a";

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
            const cfg = IMPACT[item.level] ?? { color: "#71767a", pct: 30 };
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

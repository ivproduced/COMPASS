const impactLevels = [
  { label: "Confidentiality", level: "HIGH", color: "#EF4444", pct: 80 },
  { label: "Integrity", level: "MODERATE", color: "#F59E0B", pct: 60 },
  { label: "Availability", level: "MODERATE", color: "#F59E0B", pct: 60 },
];

const ClassifyTab = () => (
  <>
    {/* Badge */}
    <div className="flex flex-col items-center gap-2">
      <span className="bg-[#F59E0B] text-white font-bold text-sm px-4 py-1.5 rounded-lg">
        MODERATE
      </span>
      <span className="text-[13px] text-muted-foreground">
        FedRAMP Moderate · 325 Controls
      </span>
    </div>

    {/* Impact Levels */}
    <div className="space-y-1.5">
      <h4 className="text-[13px] font-semibold text-foreground">Impact Levels</h4>
      <div className="space-y-3">
        {impactLevels.map((item) => (
          <div key={item.label} className="space-y-1">
            <div className="flex justify-between text-[12px]">
              <span className="text-muted-foreground">{item.label}</span>
              <span className="font-bold" style={{ color: item.color }}>
                {item.level}
              </span>
            </div>
            <div className="h-2 rounded-full bg-background">
              <div
                className="h-full rounded-full"
                style={{ width: `${item.pct}%`, backgroundColor: item.color }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Rationale */}
    <div className="space-y-1.5">
      <h4 className="text-[13px] font-semibold text-foreground">Rationale</h4>
      <p className="text-[13px] italic text-muted-foreground leading-relaxed">
        High-water-mark classification driven by PII_SSN confidentiality requirements. SSN data mandates High confidentiality per FIPS 199.
      </p>
    </div>
  </>
);

export default ClassifyTab;

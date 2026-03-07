const donutData = [
  { label: "Implemented", pct: 76, color: "#22C55E" },
  { label: "Partial", pct: 17, color: "#F59E0B" },
  { label: "Not Addressed", pct: 7, color: "#EF4444" },
];

const documents = [
  { icon: "📄", title: "System Security Plan (SSP)" },
  { icon: "📄", title: "Plan of Action & Milestones (POA&M)" },
];

const oscalJson = `{
  "system-security-plan": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "title": "Customer Portal SSP",
      "last-modified": "2026-03-04T10:45:00Z",
      "version": "1.0.0",
      "oscal-version": "1.1.2"
    }
  }
}`;

/* Simple SVG donut */
const DonutChart = () => {
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <div className="flex flex-col items-center gap-3">
      <svg width="120" height="120" viewBox="0 0 120 120">
        {donutData.map((d) => {
          const dash = (d.pct / 100) * circumference;
          const currentOffset = offset;
          offset += dash;
          return (
            <circle
              key={d.label}
              cx="60"
              cy="60"
              r={radius}
              fill="none"
              stroke={d.color}
              strokeWidth="12"
              strokeDasharray={`${dash} ${circumference - dash}`}
              strokeDashoffset={-currentOffset}
              transform="rotate(-90 60 60)"
            />
          );
        })}
        <text
          x="60"
          y="60"
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-foreground text-[24px] font-bold"
          style={{ fontFamily: "var(--font-sans)" }}
        >
          76%
        </text>
      </svg>
      <div className="flex gap-4">
        {donutData.map((d) => (
          <div key={d.label} className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: d.color }} />
            {d.label} {d.pct}%
          </div>
        ))}
      </div>
    </div>
  );
};

const OscalTab = () => (
  <div className="space-y-5">
    <h3 className="text-[15px] font-semibold text-foreground">OSCAL Output</h3>

    <DonutChart />

    {documents.map((doc) => (
      <div
        key={doc.title}
        className="bg-[#0F172A] border border-[#475569] rounded-lg p-4 space-y-2"
      >
        <p className="text-[14px] font-semibold text-foreground">
          {doc.icon} {doc.title}
        </p>
        <p className="text-[12px] text-[#64748B]">OSCAL JSON v1.1.2</p>
        <p className="text-[12px] font-medium text-[#22C55E]">✅ Valid</p>
        <div className="flex gap-2 mt-1">
          <button className="h-8 px-3 text-[12px] font-medium rounded-md border border-border text-foreground hover:bg-accent transition-colors">
            Preview
          </button>
          <button className="h-8 px-3 text-[12px] font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
            ⬇ Download
          </button>
        </div>
      </div>
    ))}

    <div>
      <h4 className="text-[13px] font-semibold text-foreground mb-2">OSCAL Preview</h4>
      <pre className="font-mono text-[12px] bg-[#0F172A] border border-[#475569] rounded-md p-4 overflow-x-auto text-[#94A3B8] leading-relaxed">
        {oscalJson}
      </pre>
    </div>
  </div>
);

export default OscalTab;

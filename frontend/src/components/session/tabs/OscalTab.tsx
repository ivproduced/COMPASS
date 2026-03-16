import { useState } from "react";
import { useSession } from "@/context/SessionContext";
import { BASE_URL, api } from "@/lib/api";

/* Simple SVG donut */
const DonutChart = ({
  implemented,
  partial,
  notAddressed,
}: {
  implemented: number;
  partial: number;
  notAddressed: number;
}) => {
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const pctLabel = Math.round(implemented * 100);

  const segments = [
    { pct: implemented, color: "#22C55E", label: "Implemented" },
    { pct: partial, color: "#F59E0B", label: "Partial" },
    { pct: notAddressed, color: "#EF4444", label: "Not Addressed" },
  ];

  let offset = 0;
  return (
    <div className="flex flex-col items-center gap-3">
      <svg width="120" height="120" viewBox="0 0 120 120">
        {segments.map((d) => {
          const dash = d.pct * circumference;
          const cur = offset;
          offset += dash;
          return (
            <circle
              key={d.label}
              cx="60" cy="60" r={radius}
              fill="none"
              stroke={d.color}
              strokeWidth="12"
              strokeDasharray={`${dash} ${circumference - dash}`}
              strokeDashoffset={-cur}
              transform="rotate(-90 60 60)"
            />
          );
        })}
        <text x="60" y="60" textAnchor="middle" dominantBaseline="central"
          className="fill-foreground font-bold" style={{ fontSize: 24, fontFamily: "var(--font-sans)" }}>
          {pctLabel}%
        </text>
      </svg>
      <div className="flex gap-4">
        {segments.map((d) => (
          <div key={d.label} className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: d.color }} />
            {d.label} {Math.round(d.pct * 100)}%
          </div>
        ))}
      </div>
    </div>
  );
};

const DOC_LABELS: Record<string, string> = {
  ssp: "System Security Plan (SSP)",
  poam: "Plan of Action & Milestones (POA\u0026M)",
  assessment_results: "Assessment Results",
};

const OscalTab = () => {
  const { sessionId, oscalDocs, complianceScore, classification, refreshAssessment } = useSession();
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!sessionId) return;
    setGenerating(true);
    setGenError(null);
    try {
      await api.generateOscal(sessionId, "ssp");
      await refreshAssessment();
    } catch (e) {
      setGenError("Generation failed — try again.");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = (type: string) => {
    if (!sessionId) return;
    const a = document.createElement("a");
    a.href = `${BASE_URL}/api/oscal/${sessionId}/${type}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const implemented = complianceScore?.implemented ?? 0;
  const partial = complianceScore?.partial ?? 0;
  const notAddressed = complianceScore?.not_addressed ?? 0;
  const hasScore = complianceScore !== null;

  const seenTypes = new Set<string>();
  const uniqueDocs = oscalDocs.filter((d) => {
    if (seenTypes.has(d.type)) return false;
    seenTypes.add(d.type);
    return true;
  });

  return (
    <div className="space-y-5">
      <h3 className="text-[15px] font-semibold text-foreground">OSCAL Output</h3>

      {hasScore ? (
        <DonutChart
          implemented={implemented}
          partial={partial}
          notAddressed={notAddressed}
        />
      ) : (
        <p className="text-[13px] text-muted-foreground italic">
          Compliance score will appear after controls are mapped.
        </p>
      )}

      {uniqueDocs.length === 0 ? (
        <div className="space-y-3">
          <p className="text-[13px] text-muted-foreground italic">
            {classification
              ? "OSCAL documents haven't been generated yet for this session."
              : "OSCAL documents will be generated once the assessment is complete."}
          </p>
          {classification && (
            <div>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="h-8 px-3 text-[12px] font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {generating ? "Generating…" : "⚙ Generate OSCAL SSP"}
              </button>
              {genError && <p className="text-[12px] text-red-400 mt-1">{genError}</p>}
            </div>
          )}
        </div>
      ) : (
        uniqueDocs.map((doc) => (
          <div
            key={doc.type}
            className="bg-[#0F172A] border border-[#475569] rounded-lg p-4 space-y-2"
          >
            <p className="text-[14px] font-semibold text-foreground">
              📄 {DOC_LABELS[doc.type] ?? doc.type.toUpperCase()}
            </p>
            <p className="text-[12px] text-[#64748B]">OSCAL JSON v1.1.2</p>
            <p className="text-[12px] font-medium text-[#22C55E]">✅ Generated</p>
            <div className="flex gap-2 mt-1">
              <button
                onClick={() => handleDownload(doc.type)}
                className="h-8 px-3 text-[12px] font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                ⬇ Download
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default OscalTab;

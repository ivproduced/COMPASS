import { useParams } from "react-router-dom";
import TopNav from "@/components/TopNav";

const donutSegments = [
  { label: "Implemented", pct: 76, color: "#22C55E" },
  { label: "Partial", pct: 17, color: "#F59E0B" },
  { label: "Not Addressed", pct: 7, color: "#EF4444" },
];

const controls = [
  { id: "AC-1", name: "Policy & Procedures", status: "Implemented", statusColor: "#22C55E", notes: "All policies documented and approved." },
  { id: "AC-2", name: "Account Management", status: "Implemented", statusColor: "#22C55E", notes: "Centralized IAM with MFA enforced." },
  { id: "AC-3", name: "Access Enforcement", status: "Partial", statusColor: "#F59E0B", notes: "RBAC in place; attribute-based pending." },
  { id: "AC-4", name: "Info Flow Enforcement", status: "Gap", statusColor: "#EF4444", notes: "No DLP controls on outbound flows." },
  { id: "AC-5", name: "Separation of Duties", status: "Planned", statusColor: "#3B82F6", notes: "Scheduled for Q2 sprint." },
  { id: "SC-7", name: "Boundary Protection", status: "Gap", statusColor: "#EF4444", notes: "No WAF in front of CloudFront." },
  { id: "SC-8", name: "Transmission Confidentiality", status: "Implemented", statusColor: "#22C55E", notes: "TLS 1.3 enforced on all endpoints." },
  { id: "SC-28", name: "Protection at Rest", status: "Planned", statusColor: "#3B82F6", notes: "KMS encryption rollout in progress." },
];

const gaps = [
  {
    controlId: "SC-7",
    title: "Boundary Protection",
    issue: "No WAF identified in front of CloudFront CDN. Missing network boundary enforcement.",
    remediation: "Deploy AWS WAF with managed rule sets and configure rate limiting.",
    effort: "Weeks",
    effortColor: "#F59E0B",
  },
  {
    controlId: "AC-4",
    title: "Info Flow Enforcement",
    issue: "No payload inspection for sensitive data leakage on outbound flows.",
    remediation: "Implement AWS Macie for S3 scanning and VPC flow log anomaly detection.",
    effort: "Months",
    effortColor: "#EF4444",
  },
  {
    controlId: "AC-4(4)",
    title: "Content Check",
    issue: "No DLP controls identified for outbound data channels.",
    remediation: "Configure DLP policies in email gateway and S3 bucket policies.",
    effort: "Weeks",
    effortColor: "#F59E0B",
  },
];

const DonutChart = () => {
  const r = 48;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="flex flex-col items-center gap-4">
      <svg width="140" height="140" viewBox="0 0 140 140">
        {donutSegments.map((s) => {
          const dash = (s.pct / 100) * c;
          const cur = offset;
          offset += dash;
          return (
            <circle key={s.label} cx="70" cy="70" r={r} fill="none" stroke={s.color}
              strokeWidth="14" strokeDasharray={`${dash} ${c - dash}`}
              strokeDashoffset={-cur} transform="rotate(-90 70 70)" />
          );
        })}
        <text x="70" y="70" textAnchor="middle" dominantBaseline="central"
          className="fill-foreground font-bold" style={{ fontSize: 28, fontFamily: "var(--font-sans)" }}>
          76%
        </text>
      </svg>
      <div className="flex gap-5">
        {donutSegments.map((s) => (
          <span key={s.label} className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: s.color }} />
            {s.label} {s.pct}%
          </span>
        ))}
      </div>
    </div>
  );
};

const cardClass = "bg-[#1E293B] border border-[#475569] rounded-lg p-6";

const Report = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <TopNav pageTitle="Report" />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-foreground">Assessment Report</h1>
            <p className="text-[14px] text-[#64748B] mt-1">Session {id ?? "unknown"}</p>
          </div>

          {/* Compliance Score */}
          <div className={cardClass}>
            <h2 className="text-[15px] font-semibold text-foreground mb-5">Compliance Score</h2>
            <DonutChart />
          </div>

          {/* Control Mappings */}
          <div className={cardClass}>
            <h2 className="text-[15px] font-semibold text-foreground mb-4">Control Mappings</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-left text-[#64748B] border-b border-[#475569]">
                    <th className="pb-2 pr-4 font-medium">Control ID</th>
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Status</th>
                    <th className="pb-2 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {controls.map((c) => (
                    <tr key={c.id} className="border-b border-[#475569] last:border-b-0">
                      <td className="py-2.5 pr-4 font-mono text-[12px] text-foreground">{c.id}</td>
                      <td className="py-2.5 pr-4 text-foreground">{c.name}</td>
                      <td className="py-2.5 pr-4">
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded"
                          style={{ backgroundColor: c.statusColor + "22", color: c.statusColor }}>
                          {c.status}
                        </span>
                      </td>
                      <td className="py-2.5 text-[#94A3B8]">{c.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Gaps */}
          <div className={cardClass}>
            <h2 className="text-[15px] font-semibold text-foreground mb-4">Open Gaps</h2>
            <div className="space-y-4">
              {gaps.map((g) => (
                <div key={g.controlId} className="bg-background rounded-md p-4 border-l-2 border-destructive space-y-2">
                  <p className="text-[14px] font-semibold text-foreground">
                    <span className="font-mono text-[13px]">{g.controlId}</span> · {g.title}
                  </p>
                  <p className="text-[13px] text-[#94A3B8] leading-relaxed">{g.issue}</p>
                  <div>
                    <p className="text-[13px] font-semibold text-foreground">Remediation:</p>
                    <p className="text-[13px] text-[#94A3B8]">{g.remediation}</p>
                  </div>
                  <span className="inline-block text-[11px] font-medium px-2 py-0.5 rounded"
                    style={{ backgroundColor: g.effortColor + "22", color: g.effortColor }}>
                    Effort: {g.effort}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Export */}
          <div className={cardClass}>
            <h2 className="text-[15px] font-semibold text-foreground mb-4">Export Documents</h2>
            <div className="flex flex-wrap gap-3">
              <button className="h-10 px-5 text-[13px] font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
                ⬇ Download OSCAL SSP
              </button>
              <button className="h-10 px-5 text-[13px] font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
                ⬇ Download OSCAL POA&M
              </button>
              <button className="h-10 px-5 text-[13px] font-medium rounded-md border border-border text-foreground hover:bg-accent transition-colors">
                Preview JSON
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Report;

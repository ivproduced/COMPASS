const riskBadges = [
  { count: 3, label: "CRITICAL", emoji: "🔴", bg: "#EF4444" },
  { count: 8, label: "HIGH", emoji: "🟠", bg: "#F97316" },
  { count: 9, label: "MODERATE", emoji: "🟡", bg: "#F59E0B" },
  { count: 3, label: "LOW", emoji: "🟢", bg: "#22C55E" },
];

const gaps = [
  {
    severity: "critical" as const,
    borderColor: "#EF4444",
    emoji: "🔴",
    controlId: "SC-7",
    title: "Boundary Protection",
    body: "No Web Application Firewall (WAF) identified in front of CloudFront CDN. Missing network boundary enforcement for inbound traffic.",
    remediation:
      "Deploy AWS WAF with managed rule sets. Configure rate limiting and geo-blocking rules for CloudFront distribution.",
    effort: "Weeks",
    effortColor: "#F59E0B",
  },
  {
    severity: "high" as const,
    borderColor: "#F97316",
    emoji: "🟠",
    controlId: "AC-4(4)",
    title: "Content Check",
    body: "No payload inspection for sensitive data leakage detection on outbound flows. No DLP controls identified.",
    remediation:
      "Implement AWS Macie for S3 content scanning and configure VPC flow logs with anomaly detection.",
    effort: "Months",
    effortColor: "#EF4444",
  },
];

const GapsTab = () => (
  <div className="space-y-5">
    <div>
      <h3 className="text-[15px] font-semibold text-foreground">Gap Analysis</h3>
      <p className="text-[13px] text-[#64748B] mt-1">23 gaps found</p>
    </div>

    <div className="flex gap-2">
      {riskBadges.map((b) => (
        <div
          key={b.label}
          className="flex-1 flex flex-col items-center rounded-lg px-2 py-3"
          style={{ backgroundColor: b.bg }}
        >
          <span className="text-[20px] font-bold text-white leading-none">{b.count}</span>
          <span className="text-[10px] font-medium uppercase text-white mt-1 tracking-wide">
            {b.emoji} {b.label}
          </span>
        </div>
      ))}
    </div>

    {gaps.map((g) => (
      <div
        key={g.controlId}
        className="bg-[#0F172A] rounded-lg p-4"
        style={{ borderLeft: `3px solid ${g.borderColor}` }}
      >
        <p className="text-[14px] font-semibold text-foreground">
          {g.emoji}{" "}
          <span className="font-mono text-[13px]">{g.controlId}</span> · {g.title}
        </p>
        <p className="text-[13px] text-[#94A3B8] mt-2 leading-relaxed">{g.body}</p>
        <div className="mt-3">
          <p className="text-[13px] font-semibold text-foreground">Remediation:</p>
          <p className="text-[13px] text-[#94A3B8] leading-relaxed">{g.remediation}</p>
        </div>
        <div className="flex items-center justify-between mt-3">
          <span
            className="text-[11px] font-medium px-2 py-0.5 rounded"
            style={{ backgroundColor: g.effortColor + "22", color: g.effortColor }}
          >
            Effort: {g.effort}
          </span>
          <button className="text-[13px] font-medium text-primary hover:underline">
            [View Control ↗]
          </button>
        </div>
      </div>
    ))}
  </div>
);

export default GapsTab;

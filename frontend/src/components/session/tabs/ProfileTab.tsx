const Label = ({ children }: { children: React.ReactNode }) => (
  <p className="text-xs font-medium text-[#64748B] uppercase tracking-wider">{children}</p>
);

const Field = ({ label, value }: { label: string; value: string }) => (
  <div className="space-y-1.5">
    <Label>{label}</Label>
    <p className="text-sm text-foreground">{value}</p>
  </div>
);

const ProfileTab = () => (
  <>
    <div className="flex items-center gap-2">
      <h3 className="text-[15px] font-semibold text-foreground">System Profile</h3>
      <span className="text-muted-foreground">✏️</span>
    </div>
    <Field label="System Name" value="Customer Portal" />
    <div className="space-y-1.5">
      <Label>Data Types</Label>
      <div className="flex flex-wrap gap-2">
        {["PII", "PII_SSN", "Financial"].map((chip) => (
          <span
            key={chip}
            className="bg-background border border-border rounded-full px-2.5 py-1 text-xs font-medium text-foreground"
          >
            {chip}
          </span>
        ))}
      </div>
    </div>
    <Field label="Hosting" value="Cloud · AWS GovCloud" />
    <div className="space-y-1.5">
      <Label>Components</Label>
      <div className="space-y-1.5">
        {["React Frontend", "CloudFront CDN", "API Gateway", "Lambda Functions", "RDS PostgreSQL"].map((c) => (
          <div key={c} className="flex items-center gap-2 text-sm text-foreground">
            <span className="text-primary">☑</span>
            {c}
          </div>
        ))}
      </div>
    </div>
    <div className="border border-dashed border-border rounded-lg min-h-[80px] flex items-center justify-center">
      <p className="text-[13px] text-[#64748B]">📎 Drop architecture diagram here</p>
    </div>
  </>
);

export default ProfileTab;

import { useRef } from "react";
import { useSession } from "@/context/SessionContext";
import { api } from "@/lib/api";

// Maps internal canonical tags → human-readable FIPS 199 / sensitivity category display names.
// These are data sensitivity classifications, distinct from NIST SP 800-60 mission-based
// information types. FTI, PII, PHI, and CUI are defined by statute and agency policy.
const DATA_TYPE_LABELS: Record<string, string> = {
  // Personally Identifiable Information (OMB M-07-16)
  PII:                "Personally Identifiable Information (PII)",
  PII_SSN:            "Social Security Numbers",
  PII_BIOMETRIC:      "Biometric Data",
  PII_LOCATION:       "Location / GPS Data",
  PII_FINANCIAL:      "Financial Records",
  // Protected Health Information (HIPAA)
  PHI:                "Protected Health Information (PHI)",
  PHI_CLINICAL:       "Clinical / Electronic Health Records",
  PHI_MENTAL_HEALTH:  "Mental Health Records",
  PHI_SUBSTANCE_ABUSE:"Substance Abuse Treatment Records",
  PHI_GENETIC:        "Genetic Data",
  PHI_BILLING:        "Medical Billing & Insurance Claims",
  PHI_ADMIN:          "Healthcare Administrative Data",
  // Federal-specific statutory categories
  FTI:                "Federal Tax Information (FTI)",
  CJIS:               "Criminal Justice Information (CJIS)",
  LAW_ENFORCEMENT:    "Law Enforcement Sensitive",
  NATIONAL_SECURITY:  "National Security Information",
  // Controlled Unclassified Information (32 CFR Part 2002)
  CUI:                "Controlled Unclassified Information (CUI)",
  CUI_EXPORT:         "Export-Controlled Data (ITAR/EAR)",
  CUI_LEGAL:          "Legal Proceedings Data",
  // Payment / credentials
  PAYMENT_CARD:       "Payment Card Data (PCI)",
  AUTH_CREDENTIALS:   "Authentication Credentials",
  CRYPTOGRAPHIC_KEYS: "Cryptographic Keys",
  // General
  TRADE_SECRET:       "Trade Secrets",
  PROPRIETARY:        "Proprietary Information",
  PUBLIC:             "Publicly Available",
  INTERNAL:           "Internal Use Only",
};

const formatDataType = (tag: string) => DATA_TYPE_LABELS[tag] ?? tag;

const Label = ({ children }: { children: React.ReactNode }) => (
  <p className="text-xs font-medium text-[#64748B] uppercase tracking-wider">{children}</p>
);

const Field = ({ label, value }: { label: string; value: string }) => (
  <div className="space-y-1.5">
    <Label>{label}</Label>
    <p className="text-sm text-foreground">{value}</p>
  </div>
);

const ProfileTab = () => {
  const { sessionId, systemProfile, refreshAssessment } = useSession();
  const fileRef = useRef<HTMLInputElement>(null);

  const handleDiagramDrop = async (file: File) => {
    if (!sessionId) return;
    await api.uploadDiagram(sessionId, file);
    await refreshAssessment();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleDiagramDrop(file);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <h3 className="text-[15px] font-semibold text-foreground">System Profile</h3>
      </div>

      {systemProfile ? (
        <>
          {systemProfile.systemName && (
            <Field label="System Name" value={systemProfile.systemName} />
          )}
          {systemProfile.description && (
            <Field label="Description" value={systemProfile.description} />
          )}
          {(systemProfile.data_types?.length ?? 0) > 0 && (
            <div className="space-y-1.5">
              <Label>Sensitive Data Categories</Label>
              <div className="flex flex-wrap gap-2">
                {systemProfile.data_types!.map((chip) => (
                  <span
                    key={chip}
                    className="bg-background border border-border rounded-full px-2.5 py-1 text-xs font-medium text-foreground"
                  >
                    {formatDataType(chip)}
                  </span>
                ))}
              </div>
            </div>
          )}
          {systemProfile.hosting && (
            <Field label="Hosting" value={systemProfile.hosting} />
          )}
          {(systemProfile.components?.length ?? 0) > 0 && (
            <div className="space-y-1.5">
              <Label>Components</Label>
              <div className="space-y-1.5">
                {systemProfile.components!.map((c) => (
                  <div key={c} className="flex items-center gap-2 text-sm text-foreground">
                    <span className="text-primary">☑</span>
                    {c}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-muted-foreground italic">
          Describe your system to COMPASS to populate this profile.
        </p>
      )}

      <div
        className="border border-dashed border-border rounded-lg min-h-[80px] flex items-center justify-center cursor-pointer hover:border-primary/60 transition-colors"
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileRef.current?.click()}
      >
        <p className="text-[13px] text-[#64748B]">📎 Drop architecture diagram here</p>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleDiagramDrop(f);
          }}
        />
      </div>
    </>
  );
};

export default ProfileTab;

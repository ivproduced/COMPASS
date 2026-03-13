import { useRef } from "react";
import { useSession } from "@/context/SessionContext";
import { api } from "@/lib/api";

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
              <Label>Data Types</Label>
              <div className="flex flex-wrap gap-2">
                {systemProfile.data_types!.map((chip) => (
                  <span
                    key={chip}
                    className="bg-background border border-border rounded-full px-2.5 py-1 text-xs font-medium text-foreground"
                  >
                    {chip}
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

import { useState } from "react";
import ProfileTab from "./tabs/ProfileTab";
import ClassifyTab from "./tabs/ClassifyTab";
import ControlsTab from "./tabs/ControlsTab";
import GapsTab from "./tabs/GapsTab";
import OscalTab from "./tabs/OscalTab";

const tabs = ["Profile", "Classify", "Controls", "Gaps", "OSCAL"] as const;
type Tab = (typeof tabs)[number];

const ContextPanel = () => {
  const [activeTab, setActiveTab] = useState<Tab>("Profile");

  return (
    <aside className="w-[380px] shrink-0 bg-card border-l border-border flex flex-col">
      <div className="flex border-b border-border">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
              t === activeTab
                ? "text-foreground after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-primary shadow-[0_2px_6px_-2px_hsl(var(--primary)/0.4)]"
                : "text-[#64748B] hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {activeTab === "Profile" && <ProfileTab />}
        {activeTab === "Classify" && <ClassifyTab />}
        {activeTab === "Controls" && <ControlsTab />}
        {activeTab === "Gaps" && <GapsTab />}
        {activeTab === "OSCAL" && <OscalTab />}
      </div>
    </aside>
  );
};

export default ContextPanel;

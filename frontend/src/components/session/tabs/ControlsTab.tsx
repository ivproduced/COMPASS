import { useState } from "react";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

const filters = ["All", "Implemented", "Partial", "Planned", "Gap"] as const;

type Status = "impl" | "partial" | "gap" | "planned";

interface Control {
  id: string;
  name: string;
  status: Status;
  note?: string;
}

const statusConfig: Record<Status, { icon: string; label: string; color: string }> = {
  impl: { icon: "●", label: "Impl", color: "#22C55E" },
  partial: { icon: "◐", label: "Part", color: "#F59E0B" },
  gap: { icon: "✗", label: "Gap", color: "#EF4444" },
  planned: { icon: "◯", label: "Plan", color: "#3B82F6" },
};

const families: { name: string; mapped: number; total: number; controls: Control[] }[] = [
  {
    name: "Access Control (AC)",
    mapped: 24,
    total: 47,
    controls: [
      { id: "AC-1", name: "Policy & Procedures", status: "impl" },
      { id: "AC-2", name: "Account Management", status: "impl" },
      { id: "AC-3", name: "Access Enforcement", status: "partial" },
      { id: "AC-4", name: "Info Flow Enforcement", status: "gap" },
      { id: "AC-5", name: "Separation of Duties", status: "planned" },
    ],
  },
  {
    name: "System & Comms (SC)",
    mapped: 18,
    total: 34,
    controls: [
      {
        id: "SC-7",
        name: "Boundary Protection",
        status: "gap",
        note: "No WAF identified in front of CloudFront",
      },
      { id: "SC-8", name: "Transmission Confidentiality", status: "impl" },
      { id: "SC-28", name: "Protection at Rest", status: "planned" },
    ],
  },
];

const ControlsTab = () => {
  const [activeFilter, setActiveFilter] = useState("All");
  const [search, setSearch] = useState("");

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-semibold text-foreground">Control Mappings</h3>
        <span className="text-[13px] text-[#64748B]">147 / 325 mapped</span>
      </div>

      {/* Progress */}
      <div className="space-y-1">
        <div className="h-2 rounded-full bg-background">
          <div className="h-full rounded-full bg-primary" style={{ width: "45%" }} />
        </div>
        <p className="text-[12px] text-[#64748B]">45% coverage</p>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
              f === activeFilter
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:text-foreground"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Search */}
      <input
        type="text"
        placeholder="Search controls…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full h-9 bg-background border border-border rounded-md px-3 text-[13px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
      />

      {/* Accordion */}
      <Accordion type="multiple" defaultValue={families.map((f) => f.name)}>
        {families.map((family) => (
          <AccordionItem key={family.name} value={family.name} className="border-border">
            <AccordionTrigger className="text-[13px] font-semibold text-foreground hover:no-underline py-2.5">
              <span className="flex-1 text-left">{family.name}</span>
              <span className="text-[12px] font-normal text-muted-foreground mr-2">
                {family.mapped} / {family.total}
              </span>
            </AccordionTrigger>
            <AccordionContent className="pb-1 pt-0">
              {family.controls.map((ctrl) => {
                const cfg = statusConfig[ctrl.status];
                const isGap = ctrl.status === "gap";
                return (
                  <div key={ctrl.id}>
                    <div
                      className={`flex items-center h-9 pl-4 text-[13px] hover:bg-background rounded-sm transition-colors ${
                        isGap && ctrl.note ? "border-l-2 border-[#EF4444]" : ""
                      }`}
                    >
                      <span style={{ color: cfg.color }} className="mr-2">
                        {cfg.icon}
                      </span>
                      <span className="font-mono text-[12px] text-foreground mr-2">
                        {ctrl.id}
                      </span>
                      <span className="flex-1 text-muted-foreground truncate">
                        {ctrl.name}
                      </span>
                      <span
                        className="text-[11px] font-bold mr-1"
                        style={{ color: cfg.color }}
                      >
                        {cfg.label}
                      </span>
                    </div>
                    {ctrl.note && (
                      <p className="pl-8 text-[12px] italic text-[#EF4444] pb-1">
                        {ctrl.note}
                      </p>
                    )}
                  </div>
                );
              })}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </>
  );
};

export default ControlsTab;

import { useMemo, useState } from "react";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { useSession } from "@/context/SessionContext";
import type { ControlMapping } from "@/context/SessionContext";

const filters = ["All", "Implemented", "Partial", "Planned", "Gap"] as const;

type Status = "impl" | "partial" | "gap" | "planned";

const statusConfig: Record<Status, { icon: string; label: string; color: string }> = {
  impl: { icon: "●", label: "Impl", color: "#22C55E" },
  partial: { icon: "◐", label: "Part", color: "#F59E0B" },
  gap: { icon: "✗", label: "Gap", color: "#EF4444" },
  planned: { icon: "◯", label: "Plan", color: "#3B82F6" },
};

const FAMILY_NAMES: Record<string, string> = {
  AC: "Access Control",
  AT: "Awareness & Training",
  AU: "Audit & Accountability",
  CA: "Assessment, Authorization & Monitoring",
  CM: "Configuration Management",
  CP: "Contingency Planning",
  IA: "Identification & Authentication",
  IR: "Incident Response",
  MA: "Maintenance",
  MP: "Media Protection",
  PE: "Physical & Environmental",
  PL: "Planning",
  PM: "Program Management",
  PS: "Personnel Security",
  PT: "PII Processing & Transparency",
  RA: "Risk Assessment",
  SA: "System & Services Acquisition",
  SC: "System & Communications Protection",
  SI: "System & Information Integrity",
  SR: "Supply Chain Risk Management",
};

function toStatus(s: string): Status {
  if (s === "implemented") return "impl";
  if (s === "partial") return "partial";
  if (s === "not_implemented" || s === "gap") return "gap";
  return "planned";
}

function groupByFamily(controls: ControlMapping[]) {
  const groups: Record<
    string,
    { name: string; controls: ControlMapping[] }
  > = {};
  for (const c of controls) {
    const code = c.control_id.split("-")[0].toUpperCase();
    if (!groups[code]) {
      groups[code] = { name: FAMILY_NAMES[code] ?? code, controls: [] };
    }
    groups[code].controls.push(c);
  }
  return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
}

const ControlsTab = () => {
  const { controls, classification } = useSession();
  const [activeFilter, setActiveFilter] = useState("All");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let list = controls;
    if (activeFilter !== "All") {
      const map: Record<string, string[]> = {
        Implemented: ["implemented"],
        Partial: ["partial"],
        Planned: ["planned", "not_assessed"],
        Gap: ["not_implemented", "gap"],
      };
      list = list.filter((c) =>
        map[activeFilter]?.includes(c.implementation_status)
      );
    }
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) =>
          c.control_id.toLowerCase().includes(q) ||
          (c.control_title ?? "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [controls, activeFilter, search]);

  const families = useMemo(() => groupByFamily(filtered), [filtered]);
  const total = classification?.control_count ?? 0;
  const pct = total > 0 ? Math.round((controls.length / total) * 100) : 0;

  if (controls.length === 0) {
    return (
      <div className="flex items-center justify-center h-32">
        <p className="text-sm text-muted-foreground italic text-center">
          Control mappings will appear as COMPASS maps your system.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-semibold text-foreground">Control Mappings</h3>
        <span className="text-[13px] text-[#64748B]">
          {controls.length} / {total || "?"} mapped
        </span>
      </div>

      {total > 0 && (
        <div className="space-y-1">
          <div className="h-2 rounded-full bg-background">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-[12px] text-[#64748B]">{pct}% coverage</p>
        </div>
      )}

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

      <input
        type="text"
        placeholder="Search controls…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full h-9 bg-background border border-border rounded-md px-3 text-[13px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
      />

      {families.length === 0 ? (
        <p className="text-[13px] text-muted-foreground italic">No controls match.</p>
      ) : (
        <Accordion type="multiple" defaultValue={families.map(([k]) => k)}>
          {families.map(([code, family]) => {
            const implCount = family.controls.filter((c) =>
              ["implemented", "partial"].includes(c.implementation_status)
            ).length;
            return (
              <AccordionItem key={code} value={code} className="border-border">
                <AccordionTrigger className="text-[13px] font-semibold text-foreground hover:no-underline py-2.5">
                  <span className="flex-1 text-left">{family.name}</span>
                  <span className="text-[12px] font-normal text-muted-foreground mr-2">
                    {implCount} / {family.controls.length}
                  </span>
                </AccordionTrigger>
                <AccordionContent className="pb-1 pt-0">
                  {family.controls.map((ctrl) => {
                    const s = toStatus(ctrl.implementation_status);
                    const cfg = statusConfig[s];
                    const isGap = s === "gap";
                    return (
                      <div key={ctrl.control_id}>
                        <div
                          className={`flex items-center h-9 pl-4 text-[13px] hover:bg-background rounded-sm transition-colors ${
                            isGap ? "border-l-2 border-[#EF4444]" : ""
                          }`}
                        >
                          <span style={{ color: cfg.color }} className="mr-2">
                            {cfg.icon}
                          </span>
                          <span className="font-mono text-[12px] text-foreground mr-2">
                            {ctrl.control_id}
                          </span>
                          <span className="flex-1 text-muted-foreground truncate">
                            {ctrl.control_title ?? ""}
                          </span>
                          <span
                            className="text-[11px] font-bold mr-1"
                            style={{ color: cfg.color }}
                          >
                            {cfg.label}
                          </span>
                        </div>
                        {isGap && ctrl.implementation_description && (
                          <p className="pl-8 text-[12px] italic text-[#EF4444] pb-1">
                            {ctrl.implementation_description}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      )}
    </>
  );
};

export default ControlsTab;

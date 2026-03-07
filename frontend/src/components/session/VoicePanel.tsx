const VoicePanel = () => (
  <aside className="w-20 shrink-0 bg-card border-r border-border flex flex-col items-center py-6 gap-5">
    <button className="w-16 h-16 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-2xl hover:scale-105 transition-transform ring-2 ring-primary/60 animate-[pulse_2s_cubic-bezier(0.4,0,0.6,1)_infinite] ring-offset-2 ring-offset-card">
      🎤
    </button>
    <div className="flex items-end gap-1 h-8">
      {[14, 22, 28, 18, 10].map((h, i) => (
        <span
          key={i}
          className="w-1 rounded-full bg-[#06B6D4]"
          style={{
            height: h,
            animation: `wave 1s ease-in-out ${i * 0.15}s infinite alternate`,
          }}
        />
      ))}
    </div>
    <span className="text-[11px] font-medium text-[#22C55E]">● Live</span>
    <div className="flex flex-col items-center gap-3 mt-2">
      {[
        { label: "Intake", state: "done" },
        { label: "Classify", state: "active" },
        { label: "Mapping", state: "pending" },
        { label: "Gaps", state: "pending" },
        { label: "OSCAL", state: "pending" },
      ].map((p) => (
        <div key={p.label} className="flex flex-col items-center gap-1">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              p.state === "done"
                ? "bg-[#22C55E]"
                : p.state === "active"
                ? "bg-primary animate-pulse"
                : "border border-border bg-transparent"
            }`}
          />
          <span
            className={`text-[11px] ${
              p.state === "active" ? "text-foreground" : "text-muted-foreground"
            }`}
          >
            {p.label}
          </span>
        </div>
      ))}
    </div>
  </aside>
);

export default VoicePanel;

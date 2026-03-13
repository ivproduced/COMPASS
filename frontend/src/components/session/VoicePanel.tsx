import { useSession, type Phase } from "@/context/SessionContext";

const PHASES: { key: Phase; label: string }[] = [
  { key: "intake", label: "Intake" },
  { key: "classification", label: "Classify" },
  { key: "mapping", label: "Mapping" },
  { key: "gaps", label: "Gaps" },
  { key: "oscal", label: "OSCAL" },
];

const PHASE_ORDER: Phase[] = ["intake", "classification", "mapping", "gaps", "oscal"];

const VoicePanel = () => {
  const { phase, isConnected, isListening, startListening, stopListening } = useSession();

  const currentIdx = PHASE_ORDER.indexOf(phase);

  const handleMicClick = async () => {
    if (isListening) stopListening();
    else await startListening();
  };

  return (
    <aside className="w-20 shrink-0 bg-card border-r border-border flex flex-col items-center py-6 gap-5">
      <button
        onClick={handleMicClick}
        disabled={!isConnected}
        className={`w-16 h-16 rounded-full flex items-center justify-center text-primary-foreground text-2xl hover:scale-105 transition-transform ring-2 ring-offset-2 ring-offset-card disabled:opacity-40 ${
          isListening
            ? "bg-red-500 ring-red-400/60 animate-[pulse_2s_cubic-bezier(0.4,0,0.6,1)_infinite]"
            : "bg-primary ring-primary/60"
        }`}
        title={isListening ? "Stop" : isConnected ? "Start listening" : "Connecting…"}
      >
        {isListening ? "⏹" : "🎤"}
      </button>

      {isListening && (
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
      )}

      <span
        className={`text-[11px] font-medium ${
          isConnected ? "text-[#22C55E]" : "text-[#64748B]"
        }`}
      >
        {isConnected ? "● Live" : "○ Off"}
      </span>

      <div className="flex flex-col items-center gap-3 mt-2">
        {PHASES.map((p, i) => {
          const s = i < currentIdx ? "done" : i === currentIdx ? "active" : "pending";
          return (
            <div key={p.key} className="flex flex-col items-center gap-1">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  s === "done"
                    ? "bg-[#22C55E]"
                    : s === "active"
                    ? "bg-primary animate-pulse"
                    : "border border-border bg-transparent"
                }`}
              />
              <span
                className={`text-[11px] ${
                  s === "active" ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {p.label}
              </span>
            </div>
          );
        })}
      </div>
    </aside>
  );
};

export default VoicePanel;

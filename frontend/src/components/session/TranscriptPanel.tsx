import { useRef, useEffect, useState } from "react";
import { useSession } from "@/context/SessionContext";

const TranscriptPanel = () => {
  const { transcript, isListening, isConnected, sessionId, sendTextMessage } = useSession();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    sendTextMessage(text);
    setInput("");
  };

  return (
    <main className="flex-1 flex flex-col min-w-0 bg-background">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {transcript.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-muted-foreground italic">
              {isConnected
                ? "Start speaking or type below to begin your assessment."
                : "Connecting to COMPASS…"}
            </p>
          </div>
        ) : (
          transcript.map((entry, idx) => {
            const isCompass = entry.speaker === "compass";
            const time = new Date(entry.timestamp).toLocaleTimeString();
            return (
              <div key={idx} className={`max-w-[75%] ${isCompass ? "" : "ml-auto"}`}>
                <p
                  className={`text-xs font-medium text-[#64748B] mb-1 ${
                    isCompass ? "" : "text-right"
                  }`}
                >
                  {isCompass ? `COMPASS · ${time}` : `You · ${time}`}
                  {entry.tag && (
                    <span className="text-[#06B6D4] ml-1">{entry.tag}</span>
                  )}
                </p>
                <div
                  className={`rounded-lg p-4 ${
                    isCompass
                      ? "bg-card rounded-tl-sm"
                      : "bg-[#1B2A4A] rounded-tr-sm"
                  }`}
                >
                  <p className="text-sm text-foreground leading-relaxed">
                    {entry.text}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-3 border-t border-border space-y-2">
        {isListening && (
          <p className="text-[13px] italic text-[#64748B]">
            ● COMPASS is listening…
          </p>
        )}
        {!isConnected && sessionId && !isListening && (
          <p className="text-[12px] text-[#64748B]">
            Voice unavailable — type below to chat with COMPASS.
          </p>
        )}
        <div className="flex gap-2">
          <input
            className="flex-1 bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Or type a message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="px-3 py-2 bg-primary text-primary-foreground text-sm rounded-md disabled:opacity-40 hover:bg-primary/90 transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
};

export default TranscriptPanel;

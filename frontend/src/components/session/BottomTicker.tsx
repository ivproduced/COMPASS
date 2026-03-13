import { useSession } from "@/context/SessionContext";
import { useEffect, useState } from "react";

const BottomTicker = () => {
  const { latestEvent } = useSession();
  const [, setTick] = useState(0);

  // Re-render every 10 s so "X seconds ago" stays fresh
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 10_000);
    return () => clearInterval(id);
  }, []);

  if (!latestEvent) {
    return (
      <div className="h-12 shrink-0 bg-card border-t border-border flex items-center justify-center text-[13px] text-muted-foreground">
        Waiting for activity…
      </div>
    );
  }

  const secs = Math.round(
    (Date.now() - latestEvent.timestamp.getTime()) / 1000
  );
  const ago =
    secs < 60 ? `${secs}s ago` : `${Math.round(secs / 60)}m ago`;

  return (
    <div className="h-12 shrink-0 bg-card border-t border-border flex items-center justify-center gap-4 text-[13px] text-muted-foreground">
      <span>
        ● {latestEvent.label}{" "}
        <span className="text-muted-foreground/60">· {ago}</span>
      </span>
    </div>
  );
};

export default BottomTicker;

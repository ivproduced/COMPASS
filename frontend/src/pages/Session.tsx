import { useEffect } from "react";
import { useParams } from "react-router-dom";
import TopNav from "@/components/TopNav";
import VoicePanel from "@/components/session/VoicePanel";
import TranscriptPanel from "@/components/session/TranscriptPanel";
import ContextPanel from "@/components/session/ContextPanel";
import BottomTicker from "@/components/session/BottomTicker";
import { SessionProvider, useSession } from "@/context/SessionContext";

function SessionInner() {
  const { id } = useParams<{ id: string }>();
  const { connect, disconnect } = useSession();

  useEffect(() => {
    if (id) connect(id);
    return () => disconnect();
  }, [id, connect, disconnect]);

  return (
    <div className="h-screen flex flex-col bg-background">
      <TopNav pageTitle={id ? `Session ${id.slice(0, 8)}…` : "Session"} editable sessionId={id} />

      <div className="flex-1 flex min-h-0">
        <VoicePanel />
        <TranscriptPanel />
        <ContextPanel />
      </div>

      <BottomTicker />

      <style>{`
        @keyframes wave {
          0% { transform: scaleY(0.5); }
          100% { transform: scaleY(1.3); }
        }
      `}</style>
    </div>
  );
}

const Session = () => (
  <SessionProvider>
    <SessionInner />
  </SessionProvider>
);

export default Session;

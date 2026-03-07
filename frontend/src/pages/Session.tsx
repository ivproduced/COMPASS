import { useParams } from "react-router-dom";
import TopNav from "@/components/TopNav";
import VoicePanel from "@/components/session/VoicePanel";
import TranscriptPanel from "@/components/session/TranscriptPanel";
import ContextPanel from "@/components/session/ContextPanel";
import BottomTicker from "@/components/session/BottomTicker";

const Session = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="h-screen flex flex-col bg-background">
      <TopNav pageTitle={`Session ${id ?? ""}`} editable />

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
};

export default Session;

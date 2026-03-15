import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

const cards = [
  {
    icon: "🎤",
    title: "Classify System",
    body: "Describe your system by voice. COMPASS extracts data types, hosting, and components automatically.",
  },
  {
    icon: "🗂️",
    title: "Map Controls",
    body: "NIST 800-53 controls mapped in real time as you describe your architecture.",
  },
  {
    icon: "📄",
    title: "Generate OSCAL",
    body: "Download valid OSCAL SSP and POA&M documents the moment your session is complete.",
  },
];

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4">
        <span className="font-sans font-bold text-base tracking-tight text-foreground">
          COMPASS
        </span>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-4">
        <h1 className="font-sans font-bold text-[48px] leading-tight text-foreground mb-2">
          COMPASS
        </h1>
        <p className="font-sans font-normal text-[20px] text-[#64748B] mb-3">
          FedRAMP Compliance Voice Agent
        </p>
        <p className="text-muted-foreground text-base text-center max-w-md mb-8">
          Talk through your FedRAMP assessment. Get OSCAL output in minutes, not months.
        </p>
        <Button
          className="h-12 px-8 rounded-lg font-semibold text-base bg-primary text-primary-foreground hover:bg-primary/90"
          onClick={() => navigate("/dashboard")}
        >
          Start Assessment →
        </Button>

        {/* Value cards */}
        <div className="flex flex-wrap justify-center gap-5 mt-16">
          {cards.map((c) => (
            <div
              key={c.title}
              className="w-[220px] bg-card border border-border rounded-lg p-6"
            >
              <span className="text-2xl">{c.icon}</span>
              <h3 className="font-semibold text-foreground mt-3 mb-2">{c.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{c.body}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Landing;

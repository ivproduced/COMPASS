import { useState } from "react";
import { Compass, Download } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface TopNavProps {
  pageTitle: string;
  editable?: boolean;
  sessionId?: string;
}

const TopNav = ({ pageTitle, editable = false, sessionId }: TopNavProps) => {
  const navigate = useNavigate();
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!sessionId) return;
    setExporting(true);
    try {
      const { download_url } = await api.generateOscal(sessionId, "ssp");
      window.open(download_url, "_blank");
    } catch {
      // silent
    } finally {
      setExporting(false);
    }
  };

  return (
    <nav
      className="h-14 w-full flex items-center justify-between px-4 shrink-0"
      style={{ backgroundColor: "hsl(var(--header-bg))", color: "hsl(var(--header-fg))" }}
    >
      {/* Left: Wordmark */}
      <button onClick={() => navigate("/")} className="flex items-center gap-2 cursor-pointer">
        <Compass className="h-5 w-5 text-white" />
        <span className="text-white font-semibold text-base tracking-tight">
          COMPASS
        </span>
      </button>

      {/* Center: Page title */}
      <div className="absolute left-1/2 -translate-x-1/2">
        {editable ? (
          <input
            defaultValue={pageTitle}
            className="bg-transparent text-white text-sm font-medium text-center border-b border-transparent hover:border-white/40 focus:border-white focus:outline-none transition-colors px-2 py-1"
          />
        ) : (
          <span className="text-white text-sm font-medium">{pageTitle}</span>
        )}
      </div>

      {/* Right: Export */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5 border-white/30 text-white hover:bg-white/10 hover:text-white bg-transparent"
          onClick={handleExport}
          disabled={!sessionId || exporting}
        >
          <Download className="h-4 w-4" />
          {exporting ? "Generating…" : "Export"}
        </Button>
      </div>
    </nav>
  );
};

export default TopNav;

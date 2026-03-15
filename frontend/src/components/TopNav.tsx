import { Compass, Download } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface TopNavProps {
  pageTitle: string;
  editable?: boolean;
}

const TopNav = ({ pageTitle, editable = false }: TopNavProps) => {
  const navigate = useNavigate();
  return (
    <nav className="h-14 w-full bg-card border-b border-border flex items-center justify-between px-4 shrink-0">
      {/* Left: Wordmark */}
      <button onClick={() => navigate("/")} className="flex items-center gap-2 cursor-pointer">
        <Compass className="h-5 w-5 text-primary" />
        <span className="text-foreground font-semibold text-base tracking-tight">
          COMPASS
        </span>
      </button>

      {/* Center: Page title */}
      <div className="absolute left-1/2 -translate-x-1/2">
        {editable ? (
          <input
            defaultValue={pageTitle}
            className="bg-transparent text-foreground text-sm font-medium text-center border-b border-transparent hover:border-border focus:border-primary focus:outline-none transition-colors px-2 py-1"
          />
        ) : (
          <span className="text-foreground text-sm font-medium">{pageTitle}</span>
        )}
      </div>

      {/* Right: Export + Avatar */}
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" className="gap-1.5 text-muted-foreground">
          <Download className="h-4 w-4" />
          Export
        </Button>

      </div>
    </nav>
  );
};

export default TopNav;

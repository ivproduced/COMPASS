const BottomTicker = () => (
  <div className="h-12 shrink-0 bg-card border-t border-border flex items-center justify-center gap-4 text-[13px] text-muted-foreground">
    <button className="hover:text-foreground transition-colors">◀</button>
    <span>
      ● Mapped <span className="font-mono">AC-2</span> (Account Management) → Implemented · 5 seconds ago
    </span>
    <button className="hover:text-foreground transition-colors">▶</button>
  </div>
);

export default BottomTicker;

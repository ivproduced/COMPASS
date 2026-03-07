const TranscriptPanel = () => (
  <main className="flex-1 flex flex-col min-w-0 bg-background">
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      <div className="max-w-[75%]">
        <p className="text-xs font-medium text-[#64748B] mb-1">COMPASS · 10:32:01</p>
        <div className="bg-card rounded-lg rounded-tl-sm p-4">
          <p className="text-sm text-foreground leading-relaxed">
            Welcome. I'm COMPASS, your FedRAMP compliance mapping assistant. Can you start by describing your system and the types of data it processes?
          </p>
        </div>
      </div>
      <div className="max-w-[75%] ml-auto">
        <p className="text-xs font-medium text-[#64748B] mb-1 text-right">You · 10:32:15</p>
        <div className="bg-[#1B2A4A] rounded-lg rounded-tr-sm p-4">
          <p className="text-sm text-foreground leading-relaxed">
            We're building a customer portal that processes PII — names, SSNs, and financial records. It's hosted on AWS GovCloud.
          </p>
        </div>
      </div>
      <div className="max-w-[75%]">
        <p className="text-xs font-medium text-[#64748B] mb-1">
          COMPASS · 10:32:28{" "}
          <span className="text-[#06B6D4] ml-1">[Classified]</span>
        </p>
        <div className="bg-card rounded-lg rounded-tl-sm p-4 space-y-3">
          <p className="text-sm text-foreground leading-relaxed">
            Based on PII including SSNs and financial records, I'm classifying this as FIPS 199 Moderate with High confidentiality impact.
          </p>
          <div className="bg-background border border-border rounded-md p-3 space-y-2">
            <p className="text-[13px] font-semibold text-foreground">📋 Classification Result</p>
            {[
              ["Confidentiality", "High"],
              ["Integrity", "Moderate"],
              ["Availability", "Moderate"],
              ["Baseline", "FedRAMP Moderate · 325 Controls"],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between text-[13px]">
                <span className="text-muted-foreground">{label}</span>
                <span className="text-foreground">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
    <div className="px-6 py-3 border-t border-border">
      <p className="text-[13px] italic text-[#64748B]">● COMPASS is listening...</p>
    </div>
  </main>
);

export default TranscriptPanel;

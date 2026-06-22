import { useState } from "react";

/**
 * USWDS-style official U.S. government website banner.
 * Appears at the very top of every page, above the site header.
 * Ref: https://designsystem.digital.gov/components/banner/
 */
const GovBanner = () => {
  const [expanded, setExpanded] = useState(false);

  return (
    <section
      className="w-full bg-[#f0f0f0] border-b border-[#dfe1e2] text-[#1b1b1b]"
      aria-label="Official website of the United States government"
    >
      <div className="max-w-[1200px] mx-auto px-4">
        {/* Collapsed header row */}
        <div className="flex items-center justify-between py-1.5">
          <div className="flex items-center gap-2">
            {/* US Flag SVG */}
            <svg
              aria-hidden="true"
              className="shrink-0"
              width="16"
              height="11"
              viewBox="0 0 16 11"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect width="16" height="11" fill="#B22234" />
              <rect y="1.57143" width="16" height="0.785714" fill="white" />
              <rect y="3.14286" width="16" height="0.785714" fill="white" />
              <rect y="4.71429" width="16" height="0.785714" fill="white" />
              <rect y="6.28571" width="16" height="0.785714" fill="white" />
              <rect y="7.85714" width="16" height="0.785714" fill="white" />
              <rect y="9.42857" width="16" height="0.785714" fill="white" />
              <rect width="6.4" height="5.5" fill="#3C3B6E" />
            </svg>
            <p className="text-[12px] text-[#1b1b1b]">
              An official website of the United States government
            </p>
          </div>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-[12px] font-medium text-[#005ea2] underline decoration-dotted hover:text-[#1a4480] focus:outline-none"
            aria-expanded={expanded}
          >
            Here's how you know
            <svg
              aria-hidden="true"
              width="10"
              height="6"
              viewBox="0 0 10 6"
              fill="currentColor"
              className={`transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
            >
              <path d="M0 0L5 6L10 0H0Z" />
            </svg>
          </button>
        </div>

        {/* Expanded panel */}
        {expanded && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-4 pt-1 text-[13px] text-[#1b1b1b]">
            <div className="flex gap-3">
              <span className="text-[18px] shrink-0">🏛️</span>
              <div>
                <p className="font-semibold mb-0.5">Official websites use .gov</p>
                <p className="text-[#565c65]">
                  A <strong>.gov</strong> website belongs to an official government organization in the United States.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-[18px] shrink-0">🔒</span>
              <div>
                <p className="font-semibold mb-0.5">Secure .gov websites use HTTPS</p>
                <p className="text-[#565c65]">
                  A <strong>lock</strong> or <strong>https://</strong> means you've safely connected to the .gov website. Share sensitive information only on official, secure sites.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default GovBanner;

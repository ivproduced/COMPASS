# COMPASS Frontend — Your Role & Getting Started

> This document is written for you specifically. It covers what your role is, what you need to learn, and exactly how to get started. Nothing is assumed except that you've used VS Code and Lovable before.

---

## Your Role on This Project

You own the frontend. That means everything judges and users see when they open COMPASS — the landing page, the session dashboard, and most importantly the live assessment view where voice, transcript, and compliance data appear together in real time. Your husband owns everything behind the scenes (the AI voice agent, the server, the database). Your job is to make the interface look and feel authoritative, professional, and technically impressive.

You are not expected to understand how the voice pipeline or AI agents work. You are expected to build something that makes judges lean forward.

**Your deliverable by March 15:** A working React app with four views. The three-column Session view is the most important thing — it's the "wow" moment for judges. Get that right first.

**You are not alone.** Every time you get stuck — whether it's a Lovable prompt that produced something wrong, a layout that won't behave, or something in VS Code you don't understand — bring it here. Paste what you see, describe what you expected, and we'll fix it together.

---

## What COMPASS Actually Does (So You Can Build It Accurately)

COMPASS is a voice-first FedRAMP compliance tool. Here's the user flow you're building a UI for:

1. User opens the app, logs in, lands on a **dashboard** showing their past assessments
2. User clicks **New Session** — a three-column assessment view opens
3. User clicks the **microphone** and describes their system out loud ("We're building a customer portal that handles SSNs and financial records on AWS GovCloud…")
4. COMPASS **speaks back** in real time, asking follow-up questions, classifying the system, and mapping NIST 800-53 security controls
5. As the conversation happens, the **right panel** fills in automatically — system profile, classification result, control mappings, gaps, and finally OSCAL output documents
6. A **bottom ticker** shows each event as it happens ("● Mapped AC-2 → Implemented")
7. When done, the user downloads generated OSCAL compliance documents

Your job is to build the UI that makes this feel like a real, authoritative compliance tool — not a demo.

---

## What You Need to Learn (And How)

You don't need to become a developer. You need to become fluent enough in specific areas to build and maintain this one app. Here's the list, in priority order.

---

### 1. Lovable — Your Primary Tool

**What it is:** An AI tool that generates React components and pages from your text descriptions. You describe what you want, it writes the code.

**What you need to know:**
- How to start a new project in Lovable
- How to write effective prompts (be specific about layout, colors, font sizes, and behavior)
- How to iterate — when output isn't right, how to describe the specific fix
- How to export your project to VS Code when Lovable's prompting gets too slow for small edits

**How to learn it:**
- Watch: [Lovable's official YouTube channel](https://www.youtube.com/@lovable-dev) — start with the "getting started" videos
- The best way to learn Lovable is to use it. Start with Prompt 1 from the UX spec section below. See what comes out. Iterate.

**Time needed:** 1–2 hours to feel comfortable. You'll get faster quickly.

---

### 2. React Basics — Just Enough

**What it is:** The JavaScript framework Lovable generates code in. You don't need to write React from scratch, but you need to read it well enough to make targeted edits in VS Code.

**What you need to know:**
- What a component is (a reusable piece of UI)
- What `props` are (data passed into a component)
- What `state` is (data that changes and causes the UI to update) — specifically `useState`
- How to find the right component file to edit it

**What you do NOT need to know:**
- How to build a React app from scratch
- WebSocket, audio APIs, or anything that talks to the backend (your husband wires that in Week 3)
- Routing, context, reducers, or advanced hooks

**How to learn it:**
- Watch: [React in 100 Seconds — Fireship](https://www.youtube.com/watch?v=Tn6-PIqc4UM) (literally 2 minutes, good mental model)
- Watch: [useState explained in 10 minutes — Web Dev Simplified](https://www.youtube.com/watch?v=O6P86uwfdR0)
- Do NOT start a full React course. You don't need it. The two videos above are enough.

**Time needed:** 30–45 minutes.

---

### 3. Tailwind CSS — How the Styling Works

**What it is:** The styling system Lovable uses. Instead of writing separate CSS files, styles are applied directly as class names on elements. For example `bg-blue-500` makes a background blue, `text-sm` makes text small.

**What you need to know:**
- How to read Tailwind class names so you understand what the code is doing
- How to change colors, spacing, and font sizes by swapping class names
- COMPASS uses a **dark theme** by default — the app background is `#0F172A` (near-black navy), not white

**The most common classes you'll use:**
`flex`, `grid`, `grid-cols-3`, `fixed`, `w-80`, `h-full`, `p-4`, `m-2`, `text-sm`, `font-bold`, `rounded-lg`, `border`, `border-slate-700`, `bg-slate-900`, `text-slate-100`, `overflow-y-auto`

**What you do NOT need to know:**
- Custom Tailwind configuration
- Responsive breakpoints (we're designing desktop-first for the demo)
- Animations beyond what Lovable generates

**How to learn it:**
- Read: [Tailwind CSS Utility-First intro](https://tailwindcss.com/docs/utility-first) — just the first page, not the whole docs
- Bookmark: [Tailwind Cheat Sheet](https://nerdcave.com/tailwind-cheat-sheet) — use this as a reference when you want to change something

**Time needed:** 20–30 minutes to read. You'll reference the cheat sheet constantly at first, then less.

---

### 4. VS Code — Targeted Edits

**What it is:** You already have this. You'll use it after exporting from Lovable to make small, precise edits without re-prompting.

**What you need to know:**
- How to open a project folder
- How to find a file (Cmd+P on Mac — type the filename)
- How to find text within a file (Cmd+F)
- How to find text across all files (Cmd+Shift+F) — this is how you find the right component to edit
- How to save (Cmd+S) and see the change reflected

**What you do NOT need to know:**
- Terminal commands (your husband handles anything that requires the terminal)
- Git (he handles this too)
- Extensions beyond what's already installed

**Time needed:** You already know VS Code. Just practice the search shortcuts.

---

### 5. Google Fonts — One Specific Thing

**What it is:** The font library we're using. COMPASS uses **Inter** (the body font) and **JetBrains Mono** (for code, OSCAL output, and control IDs).

**How to add them if they don't load:**
Add this to the `<head>` of your `index.html` file:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

**Time needed:** 10 minutes if needed.

---

## The COMPASS Design System — Quick Reference Before You Prompt

Before you start prompting, memorize these. Your Lovable prompts will be much more accurate when you reference these exact values.

### Colors (Dark Mode Default)

| Token | Hex | Use |
|---|---|---|
| App background | `#0F172A` | The overall page background |
| Card / panel surface | `#1E293B` | Side panels, transcript bubbles, cards |
| Panel borders | `#475569` | Dividers between columns, card borders |
| Primary blue | `#2563EB` | Buttons, active states, links |
| Accent cyan | `#06B6D4` | Waveform, active mic indicator |
| Text primary | `#F8FAFC` | All body text |
| Text muted | `#64748B` | Timestamps, secondary labels |
| Status green | `#22C55E` | "Implemented" controls, connected status |
| Status amber | `#F59E0B` | "Partial" controls, caution states |
| Status red | `#EF4444` | Gaps, errors, not-implemented |
| Status blue | `#3B82F6` | Planned controls |

### Fonts

| Use | Font |
|---|---|
| All body text, labels, buttons | `Inter` |
| Control IDs (AC-2), OSCAL JSON, code | `JetBrains Mono` |

### Control Status Icons
- `●` green = Implemented
- `◐` amber = Partially Implemented
- `◯` blue = Planned
- `✗` red = Gap / Not Implemented
- `·` gray = Not Yet Assessed

---

## The Four Views You're Building

### View 1: Landing Page (`/`)
A minimal hero page. Logo, tagline, "Start Assessment" button, three value prop cards below. Goal: get the user into a session fast. Not where judges spend time — keep it clean and move on.

### View 2: Dashboard (`/dashboard`)
Three stat cards at top (Sessions, Controls Mapped, Open Gaps). Below that, a list of recent sessions — each row shows status dot, system name, baseline (Low/Moderate/High), controls mapped vs. total, and last active time. A "New Session" button top-right. Clicking a row takes you to View 3.

### View 3: Session View (`/session/:id`) — THE MOST IMPORTANT ONE
Three fixed columns side by side:

| Column | Width | What's in it |
|---|---|---|
| Left — Voice Panel | 80px | Microphone button, audio waveform, connection status, phase progress tracker (Intake → Classification → Mapping → Gaps → OSCAL) |
| Center — Transcript | Fills remaining space | Scrolling conversation. COMPASS messages left, user messages right. Timestamps. Inline action cards when things happen (e.g., classification result card). |
| Right — Context | 380px fixed | Five tabs: System Profile / Classification / Controls / Gaps / OSCAL. Fills in automatically as the conversation progresses. |

Below all three columns: a single 48px event ticker bar ("● Mapped AC-2 → Implemented · 5s ago").

### View 4: Report / Export (`/session/:id/report`)
Static summary view. Compliance score donut chart. Table of all control mappings. List of gaps with remediation notes. Download buttons for OSCAL SSP and POA&M documents.

---

## Lovable Prompts — In Order

Run these one at a time. Wait to see what comes out before running the next one. If something is wrong, describe the specific fix rather than re-running the whole prompt.

---

### Prompt 1 — App Shell & Navigation

```
Create a React app called COMPASS using Tailwind CSS.

Import Inter and JetBrains Mono from Google Fonts. Use Inter for all text and JetBrains Mono for any monospace content.

The entire app uses dark mode. The page background is #0F172A. Cards and panels use #1E293B. Borders use #475569. Primary text is #F8FAFC.

Set up basic routing with react-router-dom for four pages:
- / (Landing)
- /dashboard
- /session/:id
- /session/:id/report

Create a persistent top navigation bar, 56px tall, background #1E293B, with:
- Left: "COMPASS" wordmark in Inter 600 weight, color #F8FAFC, with a small compass icon before it
- Center: the current page name (e.g., "Dashboard" or an editable session name on the session page)
- Right: an Export button (ghost/outline style) and a user avatar circle (initials "JD")

Build a skeleton shell — each route shows just the top nav and a centered placeholder div with the page name. No content yet.
```

---

### Prompt 2 — Landing Page

```
Build the landing page at route / for the COMPASS app.

Center the content vertically and horizontally. No top nav on this page — it has its own minimal header.

Structure:
1. Top-left: "COMPASS" text logo in Inter 700, #F8FAFC
2. Top-right: "Sign In" button, outline style, #2563EB border and text

3. Hero section — centered:
   - Large heading: "COMPASS" in Inter 700, 48px, #F8FAFC
   - Subheading: "FedRAMP Compliance Voice Agent" in Inter 400, 20px, #64748B
   - Descriptive text: "Talk through your FedRAMP assessment. Get OSCAL output in minutes, not months." in #94A3B8, 16px, centered
   - A large "Start Assessment →" button below, filled #2563EB, rounded-lg, height 48px, Inter 600

4. Three value proposition cards below the hero, horizontally centered in a row, each 220px wide:
   - Card 1: icon 🎤, title "Classify System", body "Describe your system by voice. COMPASS extracts data types, hosting, and components automatically."
   - Card 2: icon 🗂️, title "Map Controls", body "NIST 800-53 controls mapped in real time as you describe your architecture."
   - Card 3: icon 📄, title "Generate OSCAL", body "Download valid OSCAL SSP and POA&M documents the moment your session is complete."
   
   Cards: background #1E293B, border #475569, rounded-lg, padding 24px

Page background #0F172A.
```

---

### Prompt 3 — Dashboard Page

```
Build the dashboard page at route /dashboard for the COMPASS app.

Use the persistent top nav from before. Below it:

Top section — three stat cards in a row, each with:  
- A large number (bold Inter 700, 36px, #F8FAFC)
- A label below (Inter 400, 14px, #64748B)
Card 1: "5" / "Total Sessions"
Card 2: "1,247" / "Controls Mapped"
Card 3: "34" / "Open Gaps"
Cards are #1E293B, border #475569, rounded-lg, padding 24px. Equal width, full row.

Below the cards — a section header row:
- Left: "Recent Sessions" in Inter 600, 18px, #F8FAFC
- Right: "+ New Session" button, filled #2563EB, rounded-md, Inter 500

Then a session list table, background #1E293B, rounded-lg, with these column headers: Status, System Name, Baseline, Progress, Last Active.

Show three mock rows:
1. ● green dot | Customer Portal | Moderate | 247 / 325 controls | 2 hours ago
2. ● amber dot | Data Analytics Platform | High | 89 / 421 controls | 1 day ago
3. ● gray dot | Internal Admin Tool | Low | 0 / 156 controls | 3 days ago

Each row is clickable (hover shows slightly lighter background). Clicking any row navigates to /session/demo-session-1.

Row text: #F8FAFC for system name, #94A3B8 for other columns. Inter 400, 14px. Row height 56px. Horizontal dividers between rows using #475569.
```

---

### Prompt 4 — Session View Shell (Three Columns)

```
Build the main session view at route /session/:id for the COMPASS app.

This is the most important page. It uses a fixed three-column layout that fills the full viewport height (minus the 56px top nav). No scrolling on the outer page — each column handles its own scrolling internally.

Column 1 — Voice Panel:
- Fixed width: 80px
- Background: #1E293B
- Right border: 1px solid #475569
- Content (vertically centered in the column):
  - A circular microphone button, 64x64px, background #2563EB, centered at top third of column. Shows a 🎤 emoji or mic icon in white. On hover: scale 1.05.
  - Below it: a small waveform visualization — five vertical bars (#06B6D4) that animate up and down. Make them CSS-animated for now (static height is fine, animation comes later).
  - Below waveform: "● Live" in Inter 500, 11px, #22C55E (green dot + text)
  - Below status: a vertical phase tracker with five stages. Each stage: a small circle + label to the right. Labels: "Intake", "Classify", "Mapping", "Gaps", "OSCAL". First stage has a filled green dot (●), second has a pulsing blue dot (◐), others are empty gray circles. Font Inter 400, 11px, #94A3B8. The active stage label is #F8FAFC.

Column 2 — Transcript Panel:
- Fills remaining width (flexible)
- Background: #0F172A
- Vertically scrollable
- Padding: 24px
- Show mock conversation entries:

  Entry 1 (COMPASS, left-aligned):
  - Speaker label "COMPASS · 10:32:01" in Inter 500, 12px, #64748B
  - Message bubble: background #1E293B, rounded-lg (only top-right round), padding 16px, max-width 75%
  - Text: "Welcome. I'm COMPASS, your FedRAMP compliance mapping assistant. Can you start by describing your system and the types of data it processes?" in Inter 400, 14px, #F8FAFC

  Entry 2 (User, right-aligned):
  - Speaker label "You · 10:32:15" in Inter 500, 12px, #64748B, right-aligned
  - Message bubble: background #1B2A4A (slightly blue), rounded-lg (only top-left round), max-width 75%, right-aligned
  - Text: "We're building a customer portal that processes PII — names, SSNs, and financial records. It's hosted on AWS GovCloud."

  Entry 3 (COMPASS, left-aligned), with a badge tag "[Classified]" in teal after the speaker label:
  - Text: "Based on PII including SSNs and financial records, I'm classifying this as FIPS 199 Moderate with High confidentiality impact."
  - Below the text, inside the bubble: an inline card, background #0F172A, border #475569, rounded-md, padding 12px, labeled "📋 Classification Result" in Inter 600, 13px. Four rows of data: "Confidentiality: High", "Integrity: Moderate", "Availability: Moderate", "Baseline: FedRAMP Moderate · 325 Controls". Font Inter 400, 13px, #94A3B8 for labels, #F8FAFC for values.

  At the bottom: "● COMPASS is listening..." in Inter 400 italic, 13px, #64748B

Column 3 — Context Panel:
- Fixed width: 380px
- Background: #1E293B
- Left border: 1px solid #475569
- Top: a tab bar with five tabs — "Profile", "Classify", "Controls", "Gaps", "OSCAL". Active tab has bottom border 2px #2563EB and text #F8FAFC. Inactive tabs: #64748B. Tab bar has bottom border 1px #475569.
- Tab content area: scrollable, padding 20px

Show "Profile" as the active tab with this content:
  - Section heading "System Profile" with a small ✏️ edit icon, Inter 600, 15px
  - Field "System Name" with value "Customer Portal" (as if it was filled in)
  - Field "Data Types" showing three chip/tag components: "PII" | "PII_SSN" | "Financial" — chips are background #0F172A, border #475569, rounded-full, padding 4px 10px, font Inter 500, 12px
  - Field "Hosting" with value "Cloud · AWS GovCloud"
  - Field "Components" with a checklist: ☑ React Frontend, ☑ CloudFront CDN, ☑ API Gateway, ☑ Lambda Functions, ☑ RDS PostgreSQL
  - Below: a diagram upload zone — dashed border #475569, rounded-lg, centered text "📎 Drop architecture diagram here" in Inter 400, 13px, #64748B. Minimum height 80px.

  Field labels: Inter 500, 12px, #64748B, uppercase letter-spacing
  Field values: Inter 400, 14px, #F8FAFC
  Vertical spacing between fields: 20px

Bottom of the full page — a fixed ticker bar, 48px tall, background #1E293B, top border 1px #475569:
Centered content: "◀     ● Mapped AC-2 (Account Management) → Implemented   ·   5 seconds ago     ▶"
Font: Inter 400, 13px, #94A3B8. The control ID "AC-2" in JetBrains Mono. Left/right arrows are clickable.
```

---

### Prompt 5 — Context Panel: Classification & Controls Tabs

```
Update the Context Panel on the session page to fill in the Classification and Controls tab content.

Classification tab content:
- A large badge at top showing "MODERATE" in Inter 700, white text, background #F59E0B (amber), rounded-lg, centered, with "FedRAMP Moderate · 325 Controls" below it in #94A3B8

- Section heading "Impact Levels" then three horizontal bar rows for C / I / A:
  - Confidentiality: filled bar #EF4444 (red) at ~80% width, label "HIGH" right-aligned in #EF4444 Inter 700, 12px
  - Integrity: filled bar #F59E0B at ~60%, label "MODERATE" in #F59E0B
  - Availability: filled bar #F59E0B at ~60%, label "MODERATE" in #F59E0B
  Bar backgrounds: #0F172A, rounded-full, height 8px

- Section heading "Rationale"
  Italic text: "High-water-mark classification driven by PII_SSN confidentiality requirements. SSN data mandates High confidentiality per FIPS 199."
  Font Inter 400 italic, 13px, #94A3B8

Controls tab content:
- Header row: "Control Mappings" Inter 600 15px, right-aligned "147 / 325 mapped" Inter 400 13px #64748B
- A full-width progress bar: background #0F172A, rounded-full, height 8px. Fill: 45% width, color #2563EB
- Below: "45% coverage" in Inter 400, 12px, #64748B

- Filter chips row: [All] [Implemented] [Partial] [Planned] [Gap] — chips with border #475569, rounded-full, padding 4px 12px, Inter 500, 12px. Active ([All]) has background #2563EB.

- A search input: placeholder "Search controls…", background #0F172A, border #475569, rounded-md, height 36px, Inter 400, 13px

- Then an accordion of control families. Show two families:

  Family 1 header: "Access Control (AC)" Inter 600 13px + right-aligned "24 / 47" in #64748B. Expandable (shown expanded).
  Children (list items, padding-left 16px, Inter 400, 13px, height 36px each, hover bg #0F172A):
  - ● AC-1  Policy & Procedures          Impl [green]
  - ● AC-2  Account Management           Impl [green]
  - ◐ AC-3  Access Enforcement           Part [amber]
  - ✗ AC-4  Info Flow Enforcement        Gap  [red]
  - ◯ AC-5  Separation of Duties         Plan [blue]
  Status icons and status labels use the control status colors. Control IDs in JetBrains Mono 12px.

  Family 2 header: "System & Comms (SC)" + "18 / 34". Shown expanded.
  - ✗ SC-7  Boundary Protection          Gap  [red]   ← full row has left border 2px #EF4444
    └─ "No WAF identified in front of CloudFront" — indented, #EF4444, italic, 12px
  - ● SC-8  Transmission Confidentiality Impl [green]
  - ◯ SC-28 Protection at Rest          Plan [blue]
```

---

### Prompt 6 — Context Panel: Gaps & OSCAL Tabs + Polish Pass

```
Add the Gaps and OSCAL tab content to the Context Panel. Then do a polish pass on the whole session page.

Gaps tab content:
- Header "Gap Analysis" + "23 gaps found" below it in #64748B

- A row of four risk count badges:
  - 3   CRITICAL   🔴   background #EF4444, white text
  - 8   HIGH       🟠   background #F97316, white text
  - 9   MODERATE   🟡   background #F59E0B, white text
  - 3   LOW        🟢   background #22C55E, white text
  Each badge: rounded-lg, padding 8px 12px, centered text, Inter 700 20px for number, Inter 500 10px uppercase for label

- Show two gap cards:

  Gap Card 1 (Critical):
  - Left border 3px #EF4444, background #0F172A, rounded-lg, padding 16px
  - Title row: 🔴 "SC-7 · Boundary Protection" — control ID in JetBrains Mono 13px, title in Inter 600 14px
  - Body: "No Web Application Firewall (WAF) identified in front of CloudFront CDN. Missing network boundary enforcement for inbound traffic." Inter 400 13px #94A3B8
  - "Remediation:" label Inter 600 12px #F8FAFC, then: "Deploy AWS WAF with managed rule sets. Configure rate limiting and geo-blocking rules for CloudFront distribution." Inter 400 13px #94A3B8
  - Footer row: "Effort: Weeks" chip (amber) + "[View Control ↗]" text button in #2563EB

  Gap Card 2 (High):
  - Left border 3px #F97316, background #0F172A, rounded-lg, padding 16px
  - Title: 🟠 "AC-4(4) · Content Check"
  - Body: "No payload inspection for sensitive data leakage detection on outbound flows. No DLP controls identified." Inter 400 13px #94A3B8
  - Remediation: "Implement AWS Macie for S3 content scanning and configure VPC flow logs with anomaly detection." Inter 400 13px #94A3B8
  - "Effort: Months" chip (red) + "[View Control ↗]"

OSCAL tab content:
- Header "OSCAL Output" Inter 600 15px

- Compliance score donut chart (use a simple CSS or SVG circle, ~120px diameter):
  - Center text: "76%" in Inter 700 24px #F8FAFC
  - Three arc segments: green (76%), amber (17%), red (7%)
  - Legend below: ■ Implemented 76%  ■ Partial 17%  ■ Not Addressed 7% — Inter 400, 12px

- Two document cards (background #0F172A, border #475569, rounded-lg, padding 16px):
  Card 1:
  - "📄 System Security Plan (SSP)" Inter 600 14px
  - "OSCAL JSON v1.1.2" #64748B 12px
  - "✅ Valid" green Inter 500 12px
  - Two buttons side by side: [Preview] outline, [⬇ Download] filled #2563EB, both rounded-md height 32px

  Card 2:
  - "📄 Plan of Action & Milestones (POA&M)" Inter 600 14px
  - Same OSCAL version + valid badge + buttons

- OSCAL preview section heading, then a code block (JetBrains Mono 12px, background #0F172A, border #475569, rounded-md, padding 16px, overflow-x-auto) showing:
{
  "system-security-plan": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {
      "title": "Customer Portal SSP",
      "last-modified": "2026-03-04T10:45:00Z",
      "version": "1.0.0",
      "oscal-version": "1.1.2"
    }
  }
}

Polish pass on session page:
- Make sure all three columns touch top to bottom with no gaps
- The ticker bar should be flush with the bottom of every column
- Ensure column widths are correct: left 80px fixed, right 380px fixed, center fills the rest exactly
- Tab bar in context panel: add a subtle bottom shadow on active tab
- Transcript messages should have 16px vertical gap between them
- Add a thin animated pulsing ring around the mic button (ring color #2563EB, pulse every 2 seconds) to suggest it's live
```

---

## Week-by-Week Plan

### Week 1 (Now through Mar 8) — Learn & Build Shell
- [ ] Watch the Lovable getting started videos (1–2 hrs)
- [ ] Watch the React useState video (30 min)
- [ ] Read the Tailwind intro page, bookmark the cheat sheet (20 min)
- [ ] Memorize the COMPASS color palette above — have it open while prompting
- [ ] Create a new Lovable project called "COMPASS Dashboard"
- [ ] Run **Prompt 1** — app shell and navigation
- [ ] Run **Prompt 2** — landing page
- [ ] Run **Prompt 3** — dashboard
- [ ] Screenshot all three and share for review

### Week 2 (Mar 8–11) — Build the Session View
- [ ] Run **Prompt 4** — three-column session shell with mock data
- [ ] Run **Prompt 5** — Classification and Controls tabs
- [ ] Run **Prompt 6** — Gaps, OSCAL tabs + polish pass
- [ ] Test the layout at full browser width — does the three-column layout hold?
- [ ] Export project from Lovable to VS Code

### Week 3 (Mar 11–13) — Report View & API Wiring
- [ ] Build the Report / Export view (`/session/:id/report`)
- [ ] Your husband will give you real API endpoints and WebSocket events — swap mock data for live calls
- [ ] You won't need to understand what the backend does — just where to put the call and what shape the data comes back in. We'll walk through that together.

### Week 4 (Mar 13–15) — Polish & Submission
- [ ] Visual polish pass across all views
- [ ] Test on a clean browser with no cached data
- [ ] Create the project banner/thumbnail image for the hackathon submission
- [ ] Help with the submission writeup

---

## How We Work Together

**When you're stuck:** Don't spend more than 15–20 minutes trying to figure something out alone. Paste the problem here — what you tried, what happened, what you expected. We'll fix it fast.

**When Lovable produces something wrong:** Don't re-run the whole prompt. Describe the specific thing that's wrong and ask for a targeted fix. For example: *"The mic button is square but it should be a circle"* is better than re-running Prompt 4 from scratch.

**When you need to edit in VS Code:** Use Cmd+Shift+F to search for a distinctive piece of text from the component you want to edit — like the word "waveform" or the text "No WAF identified". That will find the exact file and line.

**When the backend is ready (Week 3):** Your husband will share the API contract. You'll swap out the hardcoded mock data for real WebSocket messages and `fetch()` calls. You won't need to understand what the backend does — just where to put the call and what shape the data comes back in. We'll walk through that together when the time comes.

---

## Quick Reference

| Thing | Where to find it |
|---|---|
| Colors, fonts, layout rules | FRONTEND_DESIGN_SPEC.md |
| Lovable prompts (in order) | This document — section above |
| Backend API endpoints | FRONTEND_DESIGN_SPEC.md → Section 8.2 (Message Protocol) |
| Tailwind class reference | https://nerdcave.com/tailwind-cheat-sheet |
| Inter on Google Fonts | https://fonts.google.com/specimen/Inter |
| JetBrains Mono on Google Fonts | https://fonts.google.com/specimen/JetBrains+Mono |
| Lovable | https://lovable.dev |

---

## The Most Important Thing

The judges will spend 90% of their time looking at the Session view — the three-column layout with the voice panel, transcript, and context panel. That is the product. Everything else sets context for it.

Get the Session view right. Make it feel like a real compliance tool. If the layout is clean, the colors are correct, and the mock data tells a coherent story (a real system being assessed, controls being mapped, gaps being found), judges will believe it works.

You're not being asked to become an engineer in two weeks. You're being asked to own one focused piece of a well-scoped project, with clear prompts, a clear design direction, and backup whenever you need it. Run Prompt 1 and see what comes out.

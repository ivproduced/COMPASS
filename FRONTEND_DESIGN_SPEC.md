# COMPASS — Front-End Design Specification

## CO​mpliance Mapping & Policy Assessment Speech System

**Version:** 1.0  
**Date:** March 4, 2026  
**Status:** Draft

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Information Architecture](#2-information-architecture)
3. [Page & Layout Structure](#3-page--layout-structure)
4. [Component Specifications](#4-component-specifications)
5. [Design System & Tokens](#5-design-system--tokens)
6. [Interaction Patterns](#6-interaction-patterns)
7. [State Management](#7-state-management)
8. [Real-Time Data Flow](#8-real-time-data-flow)
9. [Responsive & Accessibility](#9-responsive--accessibility)
10. [Animation & Motion](#10-animation--motion)
11. [Error States & Empty States](#11-error-states--empty-states)
12. [File Structure](#12-file-structure)

---

## 1. Design Philosophy

### 1.1 Core Principles

| Principle | Description |
|---|---|
| **Voice-First, Visually Verified** | The UI is a companion to the voice experience — it shows what COMPASS is thinking, not what the user needs to type. The primary interaction is speech; the screen reinforces, never replaces. |
| **Progressive Disclosure** | Start minimal — a microphone button and transcript. Panels for controls, gaps, and OSCAL appear only as the conversation reaches those phases. |
| **Dashboard, Not Form** | This is not a traditional form wizard. It's a real-time compliance dashboard that fills itself in as the conversation progresses. |
| **Trust Through Transparency** | Every control mapping shows the control ID, source, and confidence. Every gap shows the specific requirement that's unmet. No black boxes. |
| **Federal Aesthetic** | Clean, professional, high-contrast. Inspired by government system dashboards (login.gov, cloud.gov aesthetics) — not consumer SaaS candy. |

### 1.2 Design References

- **login.gov** — Clean federal identity aesthetic
- **cloud.gov** / USWDS (U.S. Web Design System) — Federal-grade UI patterns
- **Linear** — Information density without clutter
- **Vercel Dashboard** — Developer-grade clarity

---

## 2. Information Architecture

### 2.1 Site Map

```
COMPASS App
├── / (Landing / Auth)
│   └── Sign in with Google
│
├── /dashboard
│   ├── Session List (recent assessments)
│   ├── Quick Stats (total sessions, controls mapped, gaps found)
│   └── New Session CTA
│
├── /session/:id (Main Assessment View)
│   ├── Voice Panel (always visible)
│   │   ├── Microphone control
│   │   ├── Live waveform / VAD indicator
│   │   └── Connection status
│   │
│   ├── Transcript Panel
│   │   ├── Real-time transcript
│   │   ├── Speaker labels (Architect / COMPASS)
│   │   └── Action annotations
│   │
│   ├── Context Panel (right sidebar, tabbed)
│   │   ├── Tab: System Profile
│   │   ├── Tab: Classification
│   │   ├── Tab: Controls
│   │   ├── Tab: Gaps
│   │   └── Tab: OSCAL
│   │
│   └── Diagram Viewer (overlay/modal)
│
└── /session/:id/report (Export View)
    ├── Compliance Summary
    ├── Control Mapping Table
    ├── Gap Analysis Report
    └── OSCAL Download Links
```

### 2.2 Navigation Model

- **Top-level:** Persistent top bar with logo, session name (editable), and user avatar/menu
- **In-session:** Three-column layout (voice | transcript | context) — no page navigation needed during active session
- **Context tabs:** Right panel switches context without losing voice connection or transcript scroll position

---

## 3. Page & Layout Structure

### 3.1 Landing Page (`/`)

```
┌────────────────────────────────────────────────────────────────┐
│  COMPASS Logo                                    [Sign In]     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│                      ╔══════════════════╗                      │
│                      ║     COMPASS      ║                      │
│                      ║                  ║                      │
│                      ║  FedRAMP         ║                      │
│                      ║  Compliance      ║                      │
│                      ║  Voice Agent     ║                      │
│                      ╚══════════════════╝                      │
│                                                                │
│     Talk through your FedRAMP assessment.                      │
│     Get OSCAL output in minutes, not months.                   │
│                                                                │
│              [ Start Assessment →  ]                           │
│                                                                │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│     │ Classify  │  │ Map      │  │ Generate │                  │
│     │ System    │  │ Controls │  │ OSCAL    │                  │
│     │ via Voice │  │ with AI  │  │ Output   │                  │
│     └──────────┘  └──────────┘  └──────────┘                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Hero section with logo, tagline, and CTA
- Three value proposition cards below
- Minimal — goal is to get the user into a session fast

### 3.2 Dashboard Page (`/dashboard`)

```
┌─────────────────────────────────────────────────────────────────────┐
│  COMPASS    [Dashboard]  [Docs]                   [User ▾]         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  Sessions    │  │  Controls   │  │  Open Gaps  │                │
│  │     5        │  │   1,247     │  │     34      │                │
│  │  Total       │  │  Mapped     │  │  Across all │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
│  Recent Sessions                          [ + New Session ]        │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 🟢 Customer Portal    │ Moderate │ 247/325 │ 2h ago      │      │
│  │ 🟡 Data Analytics     │ High     │ 89/421  │ 1d ago      │      │
│  │ ⚪ Internal Tool       │ Low      │ 0/156   │ 3d ago      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Stat cards at top: session count, total controls mapped, total open gaps
- Session list: status dot, system name, baseline, controls mapped/total, last active
- New Session button prominent in top-right
- Click session row → navigate to `/session/:id`

### 3.3 Session Page (`/session/:id`) — Primary View

This is where 95% of user time is spent. Three-column layout:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  COMPASS    Customer Portal Assessment                    [Export] [User ▾]  │
├─────────┬────────────────────────────────────────┬───────────────────────────┤
│ VOICE   │  TRANSCRIPT                            │  CONTEXT                  │
│         │                                        │  [Profile][Class][Ctrl]   │
│  ┌───┐  │  COMPASS (10:32:01)                    │  [Gaps][OSCAL]            │
│  │ ● │  │  "Welcome. I'm COMPASS, your          │                           │
│  │MIC│  │   FedRAMP compliance mapping           │  ┌─────────────────────┐  │
│  └───┘  │   assistant. Can you describe           │  │ System Profile      │  │
│         │   your system?"                         │  │                     │  │
│ ~~~~~~~~│                                        │  │ Name: Customer      │  │
│ waveform│  Architect (10:32:15)                   │  │       Portal        │  │
│ ~~~~~~~~│  "We're building a customer             │  │ Data: PII, SSN,     │  │
│         │   portal that processes PII —            │  │       Financial     │  │
│  Status:│   names, SSNs, and financial             │  │ Host: AWS GovCloud  │  │
│  ● Live │   records. It's on AWS GovCloud..."      │  │ Components:         │  │
│         │                                        │  │   ☑ React Frontend  │  │
│         │  COMPASS (10:32:28)                    │  │   ☑ API Gateway     │  │
│  ──────│  "Got it. Based on PII including         │  │   ☑ Lambda          │  │
│  Phase: │   SSNs and financial records, I'm         │  │   ☑ RDS PostgreSQL │  │
│  Intake │   classifying this as FIPS 199           │  │   ☑ S3 Bucket      │  │
│    ↓    │   Moderate ..."                         │  │                     │  │
│  Classif│                                        │  │ Diagram:            │  │
│    ↓    │  ● typing...                           │  │ [Upload diagram]    │  │
│  Mapping│                                        │  └─────────────────────┘  │
│    ↓    │                                        │                           │
│  Gaps   │                                        │                           │
│    ↓    │                                        │                           │
│  OSCAL  │                                        │                           │
│         │                                        │                           │
├─────────┴────────────────────────────────────────┴───────────────────────────┤
│  ◀ SC-7: Boundary Protection — Gap detected: No WAF identified ▶           │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Layout Specs:**

| Column | Width | Content |
|---|---|---|
| Left (Voice) | 80px fixed | Mic button, waveform, status, phase tracker |
| Center (Transcript) | Flexible (fill) | Scrolling transcript with speaker labels, timestamps, action badges |
| Right (Context) | 380px fixed | Tabbed panel — System Profile, Classification, Controls, Gaps, OSCAL |
| Bottom (Ticker) | 48px fixed | Live event ticker — last control mapped, last gap found |

---

## 4. Component Specifications

### 4.1 VoicePanel

**Location:** Left column, fixed  
**Purpose:** Microphone control, audio state visualization, session phase tracking

```
┌──────────┐
│          │
│   ┌──┐   │
│   │🎤│   │  ← Large circular mic button (64x64)
│   └──┘   │     States: idle (gray), listening (red pulse), 
│          │     processing (blue spin), speaking (green pulse)
│ ~~~~~~~~ │  ← Audio waveform (real-time, 60px height)
│ ~~~~~~~~ │     Architect voice: blue bars
│          │     COMPASS voice: green bars
│  ● Live  │  ← Connection status indicator
│          │
│ ──────── │  ← Phase progress tracker (vertical)
│ ● Intake │     ● = complete (green)
│ ● Classif│     ◐ = in progress (blue, animated)
│ ◐ Mapping│     ○ = upcoming (gray)
│ ○ Gaps   │
│ ○ OSCAL  │
└──────────┘
```

**Props:**
```typescript
interface VoicePanelProps {
  sessionId: string;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  micState: 'idle' | 'listening' | 'processing' | 'speaking';
  currentPhase: ConversationPhase;
  onMicToggle: () => void;
  onDisconnect: () => void;
  audioLevel: number; // 0-1, drives waveform amplitude
}
```

**Behavior:**
- Click mic to toggle listening on/off
- Waveform animates in real-time from audio levels
- Phase tracker auto-advances based on backend events
- Long-press mic → options menu (mute, disconnect, restart)

### 4.2 TranscriptPanel

**Location:** Center column, scrollable  
**Purpose:** Real-time conversation transcript with metadata

```
┌───────────────────────────────────────────┐
│                                           │
│  COMPASS · 10:32:01                       │
│  ┌───────────────────────────────────┐    │
│  │ Welcome. I'm COMPASS, your       │    │
│  │ FedRAMP compliance mapping        │    │
│  │ assistant. Let's start by         │    │
│  │ understanding your system...      │    │
│  └───────────────────────────────────┘    │
│                                           │
│  You · 10:32:15                           │
│  ┌───────────────────────────────────┐    │
│  │ We're building a customer portal  │    │  ← User messages: right-aligned
│  │ that processes PII — names, SSNs, │    │     lighter background
│  │ and financial records...          │    │
│  └───────────────────────────────────┘    │
│                                           │
│  COMPASS · 10:32:28        [Classified]   │  ← Action badge
│  ┌───────────────────────────────────┐    │
│  │ Based on PII including SSNs, I'm │    │
│  │ classifying this as FIPS 199      │    │
│  │ Moderate with High confidential-  │    │
│  │ ity impact.                       │    │
│  │                                   │    │
│  │ ┌─────────────────────────────┐   │    │  ← Inline action card
│  │ │ 📋 Classification Result     │   │    │
│  │ │ C: High  I: Mod  A: Mod    │   │    │
│  │ │ Baseline: FedRAMP Moderate  │   │    │
│  │ │ Controls: 325              │   │    │
│  │ └─────────────────────────────┘   │    │
│  └───────────────────────────────────┘    │
│                                           │
│  ● COMPASS is listening...                │  ← Typing/listening indicator
│                                           │
└───────────────────────────────────────────┘
```

**Props:**
```typescript
interface TranscriptPanelProps {
  entries: TranscriptEntry[];
  isAgentSpeaking: boolean;
  isListening: boolean;
}

interface TranscriptEntry {
  id: string;
  speaker: 'architect' | 'compass';
  text: string;
  timestamp: Date;
  actions?: TranscriptAction[];  // Inline action cards
}

interface TranscriptAction {
  type: 'classification' | 'control_mapped' | 'gap_found' | 'oscal_generated';
  summary: string;
  data: Record<string, unknown>;
}
```

**Behavior:**
- Auto-scrolls to bottom as new entries appear
- Scroll up to review history → auto-scroll pauses → "Jump to latest" fab appears
- Text streams in word-by-word as Gemini generates (typewriter effect)
- Action cards are expandable — click to see full detail in context panel
- Long-press a message → copy text, mark as important

### 4.3 ContextPanel (Tabbed Right Sidebar)

**Location:** Right column, fixed width  
**Purpose:** Structured data companion to the transcript

#### Tab: System Profile

```
┌─────────────────────────────┐
│  System Profile         [✏️] │
│                             │
│  System Name                │
│  ┌─────────────────────┐    │
│  │ Customer Portal      │    │
│  └─────────────────────┘    │
│                             │
│  Description                │
│  Customer-facing web portal │
│  processing PII including   │
│  SSNs and financial records │
│                             │
│  Data Types                 │
│  ┌────┐ ┌────────┐ ┌─────┐ │
│  │PII │ │PII_SSN │ │FIN  │ │  ← Chip/tag components
│  └────┘ └────────┘ └─────┘ │
│                             │
│  Hosting                    │
│  Cloud · AWS GovCloud       │
│                             │
│  Components (5)             │
│  ☑ React Frontend           │
│  ☑ CloudFront CDN          │
│  ☑ API Gateway              │
│  ☑ Lambda Functions         │
│  ☑ RDS PostgreSQL           │
│                             │
│  Diagram                    │
│  ┌─────────────────────┐    │
│  │  [📎 Upload or drop] │    │
│  │  architecture        │    │
│  │  diagram here        │    │
│  └─────────────────────┘    │
│                             │
└─────────────────────────────┘
```

#### Tab: Classification

```
┌─────────────────────────────┐
│  FIPS 199 Classification    │
│                             │
│  ┌───────────────────────┐  │
│  │ Overall: MODERATE     │  │  ← Large badge, color-coded
│  │ FedRAMP Moderate      │  │
│  │ 325 Controls          │  │
│  └───────────────────────┘  │
│                             │
│  Impact Levels              │
│  ┌─────────────────────┐   │
│  │ Confidentiality      │   │
│  │ ████████████░░ HIGH  │   │  ← Bar chart per C/I/A
│  │                      │   │
│  │ Integrity             │   │
│  │ ████████░░░░░ MOD   │   │
│  │                      │   │
│  │ Availability          │   │
│  │ ████████░░░░░ MOD   │   │
│  └─────────────────────┘   │
│                             │
│  Data Type Impacts          │
│  PII_SSN → C:H I:H A:M    │
│  Financial → C:M I:H A:M   │
│                             │
│  Rationale                  │
│  "High-water-mark driven   │
│   by PII_SSN confidential- │
│   ity and integrity..."     │
│                             │
└─────────────────────────────┘
```

#### Tab: Controls

```
┌─────────────────────────────┐
│  Control Mappings           │
│  147 / 325 mapped           │
│  ┌─────────────────────┐    │
│  │██████████░░░░░ 45%  │    │  ← Overall progress bar
│  └─────────────────────┘    │
│                             │
│  [All] [Impl] [Partial]    │  ← Filter chips
│  [Planned] [Gap]            │
│                             │
│  🔍 Search controls...      │  ← Search bar
│                             │
│  Access Control (AC)  24/47 │  ← Family accordion
│  ├─ AC-1  ● Policy     Impl│
│  ├─ AC-2  ● Accounts   Impl│
│  ├─ AC-3  ● Enforce    Part│
│  ├─ AC-4  ◐ Flow       Part│  ← Yellow = partial
│  │   └─ AC-4(4) Content ✗  │  ← Red = gap
│  ├─ AC-5  ● Sep.Duties Impl│
│  └─ ...                     │
│                             │
│  Audit (AU)          12/20  │
│  ├─ AU-1  ● Policy     Impl│
│  ├─ AU-2  ● Events     Impl│
│  └─ ...                     │
│                             │
│  System Comms (SC)   18/34  │
│  ├─ SC-7  ✗ Boundary   Gap │  ← Red highlight
│  │   └─ "No WAF detected"  │
│  └─ ...                     │
│                             │
└─────────────────────────────┘
```

**Status Icons:**
| Icon | Status | Color |
|---|---|---|
| ● | Implemented | `green-500` |
| ◐ | Partially Implemented | `amber-500` |
| ◯ | Planned | `blue-400` |
| ✗ | Not Implemented / Gap | `red-500` |
| · | Not Yet Assessed | `gray-400` |

#### Tab: Gaps

```
┌─────────────────────────────┐
│  Gap Analysis               │
│  23 gaps found              │
│                             │
│  By Risk Level              │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
│  │ 3 │ │ 8 │ │ 9 │ │ 3 │  │  ← Risk count badges
│  │CRT│ │HI │ │MOD│ │LOW│  │
│  │🔴 │ │🟠 │ │🟡 │ │🟢 │  │
│  └───┘ └───┘ └───┘ └───┘  │
│                             │
│  ┌─────────────────────┐    │
│  │ 🔴 SC-7 Boundary    │    │
│  │    Protection        │    │
│  │ No WAF in front of  │    │
│  │ CloudFront. Missing  │    │
│  │ network boundary     │    │
│  │ enforcement.         │    │
│  │                      │    │
│  │ Remediation:         │    │
│  │ Deploy AWS WAF with  │    │
│  │ rate limiting and    │    │
│  │ geo-blocking rules.  │    │
│  │                      │    │
│  │ Effort: Weeks        │    │
│  │ [View Control ↗]     │    │
│  └─────────────────────┘    │
│                             │
│  ┌─────────────────────┐    │
│  │ 🟠 AC-4(4) Content  │    │
│  │    Check             │    │
│  │ No payload inspect-  │    │
│  │ ion for sensitive     │    │
│  │ data leakage...      │    │
│  └─────────────────────┘    │
│                             │
└─────────────────────────────┘
```

#### Tab: OSCAL

```
┌─────────────────────────────┐
│  OSCAL Output               │
│                             │
│  Compliance Score           │
│  ┌─────────────────────┐    │
│  │                      │    │
│  │     ┌─────┐          │    │
│  │     │ 76% │          │    │  ← Donut chart
│  │     └─────┘          │    │
│  │  ■ Implemented  76%  │    │
│  │  ■ Partial      17%  │    │
│  │  ■ Not Addr.     7% │    │
│  └─────────────────────┘    │
│                             │
│  Documents                  │
│  ┌─────────────────────┐    │
│  │ 📄 System Security   │    │
│  │    Plan (SSP)        │    │
│  │    OSCAL JSON v1.1.2 │    │
│  │    ✅ Valid            │    │
│  │    [Preview] [⬇ DL]  │    │
│  └─────────────────────┘    │
│  ┌─────────────────────┐    │
│  │ 📄 Plan of Action &  │    │
│  │    Milestones (POA&M)│    │
│  │    OSCAL JSON v1.1.2 │    │
│  │    ✅ Valid            │    │
│  │    [Preview] [⬇ DL]  │    │
│  └─────────────────────┘    │
│                             │
│  OSCAL Preview              │
│  ┌─────────────────────┐    │
│  │ {                    │    │
│  │   "system-security-  │    │  ← Syntax-highlighted JSON
│  │    plan": {           │    │     with collapsible sections
│  │     "uuid": "...",    │    │
│  │     "metadata": {     │    │
│  │       ...             │    │
│  └─────────────────────┘    │
│                             │
└─────────────────────────────┘
```

### 4.4 DiagramViewer (Modal/Overlay)

```
┌────────────────────────────────────────────────────────────────┐
│  Architecture Diagram Analysis                          [✕]   │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                                                      │      │
│  │                                                      │      │
│  │          [Uploaded Architecture Diagram]              │      │
│  │           with AI-annotated overlays:                 │      │
│  │                                                      │      │
│  │    ┌──────────┐    ┌──────────┐    ┌──────────┐     │      │
│  │    │React App │───▶│CloudFront│───▶│API Gw    │     │      │
│  │    └──────────┘    └────┬─────┘    └────┬─────┘     │      │
│  │                    ⚠️ No WAF            │            │      │
│  │                                    ┌────▼─────┐     │      │
│  │                                    │ Lambda   │     │      │
│  │                                    └────┬─────┘     │      │
│  │                                    ┌────▼─────┐     │      │
│  │                                    │ RDS      │     │      │
│  │                                    │ ⚠️ Encrypt│     │      │
│  │                                    └──────────┘     │      │
│  │                                                      │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                │
│  Components Identified (5)        Gaps Detected (2)           │
│  ☑ React Frontend                 ⚠️ SC-7: No WAF             │
│  ☑ CloudFront CDN                ⚠️ SC-28: RDS encryption?    │
│  ☑ API Gateway                                                │
│  ☑ Lambda Functions                                           │
│  ☑ RDS PostgreSQL                                             │
│                                                                │
│                               [Close] [Discuss with COMPASS]  │
└────────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Opens when diagram is uploaded or when clicking diagram thumbnail in System Profile tab
- Diagram is pannable and zoomable (pinch on touch, scroll wheel on desktop)
- AI annotations overlay on top of diagram (positioned approximately by vision analysis)
- Annotations are colored: green = looks good, amber = needs verification, red = gap detected
- "Discuss with COMPASS" button starts a voice turn about the diagram

### 4.5 EventTicker (Bottom Bar)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ◀  ● Mapped AC-2 (Account Management) → Implemented  │  5s ago          ▶ │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Purpose:** Scrolling ticker of real-time events — control mappings, gap detections, classification updates.

**Specs:**
- Single line, 48px height, fixed at bottom
- Auto-rotates through recent events (last 10)
- Left/right arrows for manual navigation
- Click event → jumps to relevant transcript entry and context tab

---

## 5. Design System & Tokens

### 5.1 Color Palette

```
Primary:
  compass-navy:    #1B2A4A    ← Headers, primary text, nav background
  compass-blue:    #2563EB    ← Interactive elements, links, in-progress
  compass-cyan:    #06B6D4    ← Accents, waveform, active states

Status:
  status-green:    #22C55E    ← Implemented, connected, success
  status-amber:    #F59E0B    ← Partial, warning, in-progress
  status-red:      #EF4444    ← Gap, error, critical
  status-blue:     #3B82F6    ← Planned, info

Surfaces:
  surface-bg:      #0F172A    ← App background (dark mode default)
  surface-card:    #1E293B    ← Card backgrounds
  surface-hover:   #334155    ← Hover states
  surface-border:  #475569    ← Borders, dividers

Text:
  text-primary:    #F8FAFC    ← Primary text
  text-secondary:  #94A3B8    ← Secondary text, labels
  text-muted:      #64748B    ← Muted, disabled text

Light mode overrides:
  surface-bg:      #F8FAFC
  surface-card:    #FFFFFF
  surface-hover:   #F1F5F9
  surface-border:  #E2E8F0
  text-primary:    #0F172A
  text-secondary:  #475569
  text-muted:      #94A3B8
```

### 5.2 Typography

```
Font Family:
  sans:     'Inter', system-ui, -apple-system, sans-serif
  mono:     'JetBrains Mono', 'Fira Code', monospace

Scale:
  text-xs:    12px / 16px    ← Timestamps, badges
  text-sm:    14px / 20px    ← Secondary text, chip labels
  text-base:  16px / 24px    ← Body text, transcript
  text-lg:    18px / 28px    ← Section headers
  text-xl:    20px / 28px    ← Panel titles
  text-2xl:   24px / 32px    ← Page titles
  text-4xl:   36px / 40px    ← Hero heading (landing only)

Weights:
  regular:    400    ← Body text
  medium:     500    ← Labels, secondary headings
  semibold:   600    ← Panel titles, control IDs
  bold:       700    ← Page headings, metrics
```

### 5.3 Spacing

```
Base unit: 4px

space-1:    4px       ← Inline padding, icon gaps
space-2:    8px       ← Chip padding, tight stacking
space-3:    12px      ← Card internal padding
space-4:    16px      ← Section gaps, list item padding
space-5:    20px      ← Panel padding
space-6:    24px      ← Column gaps
space-8:    32px      ← Section separators
space-12:   48px      ← Major section breaks
space-16:   64px      ← Page margins (desktop)
```

### 5.4 Border Radius

```
rounded-sm:    4px       ← Tags, badges
rounded-md:    8px       ← Cards, buttons
rounded-lg:    12px      ← Panels, modals
rounded-xl:    16px      ← Image containers
rounded-full:  9999px    ← Mic button, status dots, avatars
```

### 5.5 Shadows (Dark Mode)

```
shadow-sm:     0 1px 2px rgba(0,0,0,0.3)          ← Subtle lift
shadow-md:     0 4px 6px rgba(0,0,0,0.4)          ← Cards
shadow-lg:     0 10px 15px rgba(0,0,0,0.5)        ← Modals, dropdowns
shadow-glow:   0 0 20px rgba(37,99,235,0.3)       ← Active mic button glow
shadow-danger: 0 0 20px rgba(239,68,68,0.3)       ← Gap highlight glow
```

### 5.6 Component Tokens

```
Button (Primary):
  bg: compass-blue
  text: white
  hover: compass-blue/90
  active: compass-blue/80
  radius: rounded-md
  padding: space-2 space-4
  height: 40px

Button (Secondary):
  bg: transparent
  border: 1px solid surface-border
  text: text-primary
  hover-bg: surface-hover

Chip/Tag:
  bg: surface-card
  border: 1px solid surface-border
  text: text-secondary
  radius: rounded-sm
  padding: space-1 space-2
  font: text-xs, medium

Card:
  bg: surface-card
  border: 1px solid surface-border
  radius: rounded-lg
  padding: space-4
  shadow: shadow-md

Input:
  bg: surface-bg
  border: 1px solid surface-border
  text: text-primary
  placeholder: text-muted
  focus-border: compass-blue
  radius: rounded-md
  height: 40px
  padding: space-2 space-3
```

---

## 6. Interaction Patterns

### 6.1 Voice Session Lifecycle

```
                    ┌─────────────┐
                    │   Page Load  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Request Mic │ ← Browser permission prompt
                    │  Permission  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Connect WS  │ ← "Connecting..." spinner on mic
                    │  /ws/live    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  COMPASS     │ ← Agent greeting plays as audio
                    │  Greets      │   + appears in transcript
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │     Active Session       │ ← Bidirectional streaming
              │  ┌──────────────────┐   │
              │  │ Architect speaks  │ ←─┤ Mic sends PCM chunks
              │  │ COMPASS responds  │ ──┤ Audio plays back
              │  │ Tools execute     │ ──┤ Context panel updates
              │  │ Repeat...         │   │
              │  └──────────────────┘   │
              └────────────┬────────────┘
                           │
                 ┌─────────▼───────────┐
                 │  Session End         │
                 │  - User clicks stop  │
                 │  - User navigates    │
                 │  - Inactivity (15m)  │
                 └─────────┬───────────┘
                           │
                 ┌─────────▼───────────┐
                 │  Save & Disconnect   │ ← State saved to Firestore
                 │  "Session paused"    │
                 └─────────────────────┘
```

### 6.2 Diagram Upload Flow

1. User drags file onto upload zone in System Profile tab (or uses file picker)
2. Upload zone shows progress bar
3. File uploads to `/api/diagrams` → stored in GCS
4. Thumbnail appears in System Profile tab
5. Diagram URL sent over WebSocket → COMPASS analyzes via vision
6. DiagramViewer modal auto-opens with annotations
7. COMPASS speaks analysis results simultaneously
8. Annotations update in real-time as COMPASS identifies components

### 6.3 Control Mapping Real-Time Updates

As COMPASS maps controls during conversation:
1. Backend emits WebSocket JSON: `{ "type": "control_mapped", "data": { "controlId": "AC-2", ... } }`
2. Controls tab updates — new control appears with slide-in animation
3. Family accordion auto-expands if new family
4. Event ticker shows "● Mapped AC-2 (Account Management) → Implemented"
5. Progress bar in Controls tab header animates to new percentage
6. If control has gap: Gaps tab badge count increments + red dot notification

### 6.4 Interruption Handling

- Gemini Live API handles server-side VAD (Voice Activity Detection)
- When architect starts speaking mid-response:
  1. COMPASS audio fades out (200ms)
  2. Transcript shows "— interrupted —" annotation
  3. Agent processes new input, responds to the redirect
  4. No state corruption — session context maintained
- Visual: speaking indicator switches from green (COMPASS) to blue (Architect) immediately

### 6.5 Session Resume

1. User clicks existing session on dashboard
2. Page loads → WebSocket connects → backend loads Firestore state
3. COMPASS greets: "Welcome back. We were working on [System Name]. We've mapped [N] of [Total] controls so far. Shall we continue with [current phase]?"
4. All panels populated from persisted state
5. Transcript loads last 50 entries (paginate older on scroll-up)

---

## 7. State Management

### 7.1 Store Architecture (Zustand)

```typescript
// stores/sessionStore.ts
interface SessionStore {
  // Connection
  connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';
  webSocket: WebSocket | null;
  
  // Session
  sessionId: string | null;
  currentPhase: ConversationPhase;
  
  // System Profile
  systemProfile: SystemProfile | null;
  
  // Classification
  classification: Classification | null;
  
  // Control Mappings
  controlMappings: Map<string, ControlMapping>;
  controlFamilies: ControlFamily[];
  
  // Gap Findings
  gapFindings: GapFinding[];
  
  // OSCAL
  oscalDocuments: OSCALDocument[];
  complianceScore: ComplianceScore | null;
  
  // Transcript
  transcriptEntries: TranscriptEntry[];
  
  // Audio
  micState: MicState;
  audioLevel: number;
  
  // Actions
  connect: (sessionId: string) => Promise<void>;
  disconnect: () => void;
  toggleMic: () => void;
  sendAudio: (chunk: ArrayBuffer) => void;
  uploadDiagram: (file: File) => Promise<void>;
  exportSession: () => Promise<string>;
}

type ConversationPhase =
  | 'intake'
  | 'classification'
  | 'mapping'
  | 'gap_analysis'
  | 'oscal_generation'
  | 'complete';

type MicState = 'idle' | 'listening' | 'processing' | 'speaking';
```

### 7.2 Real-Time Update Flow

```
WebSocket Message
       │
       ▼
┌──────────────┐
│  Message      │
│  Router       │ ← Parses JSON type field
└──────┬───────┘
       │
       ├── type: "transcript"     → transcriptEntries.push()
       ├── type: "phase_change"   → currentPhase = payload.phase
       ├── type: "classification" → classification = payload
       ├── type: "control_mapped" → controlMappings.set(id, payload)
       ├── type: "gap_found"      → gapFindings.push(payload)
       ├── type: "oscal_ready"    → oscalDocuments.push(payload)
       ├── type: "profile_update" → systemProfile = merge(current, payload)
       └── type: "audio"          → audioPlayer.enqueue(payload.data)
```

### 7.3 Hooks

```typescript
// hooks/useLiveAPI.ts
function useLiveAPI(sessionId: string) {
  // Manages WebSocket lifecycle
  // Handles audio capture (MediaRecorder → PCM conversion)
  // Routes incoming messages to store
  // Provides: connect(), disconnect(), sendAudio(), connectionStatus
}

// hooks/useSession.ts
function useSession(sessionId: string) {
  // Loads session from Firestore on mount
  // Subscribes to real-time Firestore updates (for multi-tab sync)
  // Provides: session, loading, error, refresh()
}

// hooks/useAudioCapture.ts
function useAudioCapture() {
  // Manages MediaStream and AudioWorklet
  // Outputs PCM 16kHz mono chunks
  // Provides: start(), stop(), audioLevel, isCapturing
}

// hooks/useAudioPlayback.ts
function useAudioPlayback() {
  // Manages AudioContext for playback
  // Queues incoming audio chunks
  // Handles playback interruption on user speech
  // Provides: play(), stop(), isPlaying
}
```

---

## 8. Real-Time Data Flow

### 8.1 Audio Pipeline

```
┌──────────────┐    PCM 16kHz    ┌──────────────┐    Gemini        ┌──────────┐
│  Microphone   │ ──────────── ▶ │  WebSocket    │ ──────────── ▶ │ Gemini   │
│  (AudioWorklet│    mono         │  Client       │  LiveClient    │ Live API │
│   → PCM)      │                │               │  RealtimeInput │          │
└──────────────┘                 │               │                │          │
                                 │               │ ◀──────────── │          │
┌──────────────┐    PCM audio    │               │  Audio +       │          │
│  Speaker      │ ◀──────────── │               │  Text +        │          │
│  (AudioContext│                │               │  Tool calls    │          │
│   playback)   │                └──────────────┘                └──────────┘
└──────────────┘

Audio Format:
  Capture: PCM, 16000 Hz, mono, 16-bit signed LE
  Playback: PCM, 24000 Hz, mono, 16-bit signed LE (Gemini output rate)
  Chunk size: ~100ms per chunk (1600 samples @ 16kHz)
```

### 8.2 Message Protocol (Client ↔ Backend WebSocket)

**Client → Backend:**

```typescript
// Audio chunk
{ type: "audio", data: ArrayBuffer }  // Raw PCM bytes

// Diagram reference (after upload)
{ type: "diagram", url: string }

// Session control
{ type: "pause" }
{ type: "resume" }
{ type: "end_session" }
```

**Backend → Client:**

```typescript
// Audio response
{ type: "audio", data: ArrayBuffer }

// Transcript update (real-time, word-by-word)
{ type: "transcript", speaker: "compass" | "architect", text: string, final: boolean }

// Phase change
{ type: "phase_change", phase: ConversationPhase, message: string }

// Classification result
{ type: "classification", data: Classification }

// Control mapped
{ type: "control_mapped", data: ControlMapping }

// Gap found
{ type: "gap_found", data: GapFinding }

// Profile update (system profile fields extracted from conversation)
{ type: "profile_update", data: Partial<SystemProfile> }

// OSCAL document ready
{ type: "oscal_ready", data: { type: "ssp" | "poam", downloadUrl: string, valid: boolean } }

// Connection status
{ type: "status", connectionStatus: string, message: string }

// Error
{ type: "error", code: string, message: string }
```

---

## 9. Responsive & Accessibility

### 9.1 Breakpoints

```
sm:     640px     ← Mobile (single column, voice + transcript only)
md:     768px     ← Tablet portrait (two columns, transcript + context stacked)
lg:     1024px    ← Tablet landscape / small desktop (full three columns)
xl:     1280px    ← Desktop (three columns with comfortable spacing)
2xl:    1536px    ← Large desktop (wider context panel, larger diagram viewer)
```

### 9.2 Responsive Layout Behavior

| Breakpoint | Layout |
|---|---|
| `< 768px` (Mobile) | Single column. Voice controls as floating bottom bar. Transcript full-width. Context panel as bottom sheet (swipe up). |
| `768px – 1023px` (Tablet) | Two columns. Voice bar at top. Transcript left (60%). Context right (40%) as collapsible sidebar. |
| `≥ 1024px` (Desktop) | Full three-column layout as specified. |

### 9.3 Mobile Voice Session

```
┌────────────────────┐
│ COMPASS   Customer │
│           Portal   │
├────────────────────┤
│                    │
│  COMPASS · 10:32   │
│  ┌──────────────┐  │
│  │ Welcome...   │  │
│  └──────────────┘  │
│                    │
│  You · 10:32       │
│  ┌──────────────┐  │
│  │ We're build- │  │
│  │ ing a custo- │  │
│  │ mer portal...│  │
│  └──────────────┘  │
│                    │
│          ...       │
│                    │
├────────────────────┤  ← Swipe up for context panel
│ Profile │ Ctrl │Gap│
├────────────────────┤
│ ~~~~~~~~  🎤  ● Live│  ← Floating bottom voice bar
└────────────────────┘
```

### 9.4 Accessibility (WCAG 2.1 AA)

| Requirement | Implementation |
|---|---|
| **Keyboard Navigation** | All interactive elements focusable via Tab. Mic toggle: Space/Enter. Tab switching: Arrow keys. |
| **Screen Reader** | ARIA live regions for transcript updates. `role="log"` on transcript. `aria-label` on all buttons. Status announcements for phase changes. |
| **Color Contrast** | All text meets 4.5:1 ratio minimum. Status colors paired with icons (not color alone). |
| **Focus Indicators** | Visible focus ring (2px compass-blue outline, 2px offset) on all interactive elements. |
| **Motion Reduction** | `prefers-reduced-motion`: disable waveform animation, disable typewriter transcript, disable slide-in animations. Use instant state changes instead. |
| **Voice-Only Mode** | The entire application is usable by voice only — no mandatory visual interaction required during a session. |
| **Text Alternatives** | All icons have `aria-label`. Diagrams get AI-generated alt text from vision analysis. |
| **Skip Links** | "Skip to transcript", "Skip to controls" visible on Tab focus. |

---

## 10. Animation & Motion

### 10.1 Transition Defaults

```css
/* Global transition */
--transition-fast:    150ms ease-out;    /* Hover, focus */
--transition-normal:  250ms ease-out;    /* Panel switches, state changes */
--transition-slow:    400ms ease-out;    /* Modal open/close, layout shifts */
```

### 10.2 Component Animations

| Component | Animation | Duration | Trigger |
|---|---|---|---|
| Mic button (idle → listening) | Scale 1.0 → 1.05, red glow pulse | 1s loop | Click mic |
| Mic button (listening → speaking) | Glow red → green, pulse synced to audio | Continuous | Agent speaks |
| Waveform bars | Height driven by audioLevel (0-100%) | 60fps | Audio stream |
| Transcript entry (new) | Fade in + slide up 8px | 250ms | New message |
| Transcript text (streaming) | Characters appear left to right | Per-char 30ms | Gemini text stream |
| Control mapping (new) | Slide in from right + fade in | 300ms | control_mapped event |
| Gap finding (new) | Slide in + brief red flash on border | 400ms | gap_found event |
| Phase tracker (advance) | Current dot pulses → shrinks to complete ● → next dot starts pulsing | 500ms | phase_change event |
| Context tab switch | Crossfade content | 200ms | Tab click |
| Progress bar (update) | Width animates to new percentage | 500ms ease-in-out | Data update |
| Event ticker | Slide left, pause 3s, slide left to next | 300ms slide + 3s pause | Auto-rotate |
| Diagram annotations | Fade in sequentially, 150ms stagger | 150ms per annotation | Vision analysis complete |
| Compliance donut chart | Segments grow from 0 to final arc | 800ms ease-out | OSCAL tab first open |

### 10.3 Reduced Motion

When `prefers-reduced-motion: reduce`:
- All animations replaced with instant opacity transitions (0 → 1, 150ms)
- Waveform shows static level indicator instead of animated bars
- Transcript text appears as full blocks, not character-by-character
- Event ticker shows static text, no sliding
- Donut chart appears fully rendered, no grow animation

---

## 11. Error States & Empty States

### 11.1 Error States

#### Microphone Permission Denied
```
┌────────────────────────────────┐
│  🎤  Microphone Access Needed   │
│                                │
│  COMPASS needs microphone      │
│  access for voice interaction. │
│                                │
│  [How to enable →]             │
│  [Continue without voice]      │
└────────────────────────────────┘
```

#### WebSocket Disconnected
```
┌────────────────────────────────┐
│  ⚡ Connection Lost             │
│                                │
│  Reconnecting...  (attempt 2/3)│
│  ████████░░░░░░░░              │
│                                │
│  Your session is saved. You    │
│  won't lose any progress.      │
│                                │
│  [Reconnect Now]               │
└────────────────────────────────┘
```

#### Tool Execution Failed (shown in transcript)
```
  COMPASS · 10:45:12     ⚠️ Retry
  ┌───────────────────────────────────┐
  │ I tried to look up controls for   │
  │ your API Gateway, but my control  │
  │ database is temporarily slow.     │
  │ Let me try a different approach   │
  │ — can you tell me more about     │
  │ how you handle authentication?    │
  └───────────────────────────────────┘
```

#### OSCAL Validation Failed
```
┌─────────────────────────────┐
│  📄 System Security Plan     │
│     OSCAL JSON v1.1.2       │
│     ❌ Validation Failed     │
│                             │
│  2 errors found:            │
│  • Missing required field:  │
│    system-id                │
│  • Invalid date format in   │
│    last-modified             │
│                             │
│  [Fix & Regenerate]         │
│  [Download Anyway]          │
└─────────────────────────────┘
```

### 11.2 Empty States

#### No Sessions Yet (Dashboard)
```
┌────────────────────────────────────────────┐
│                                            │
│        🧭                                   │
│     Welcome to COMPASS                     │
│                                            │
│  Start your first FedRAMP assessment       │
│  by describing your system to our          │
│  AI compliance assistant.                  │
│                                            │
│        [ Start First Assessment → ]        │
│                                            │
└────────────────────────────────────────────┘
```

#### No Controls Mapped Yet (Controls Tab)
```
┌─────────────────────────────┐
│  Control Mappings           │
│  0 / 325 mapped             │
│                             │
│         📋                   │
│  Controls will appear here  │
│  as COMPASS identifies them │
│  from your conversation.    │
│                             │
│  Just keep talking!         │
│                             │
└─────────────────────────────┘
```

#### No Gaps Found Yet (Gaps Tab)
```
┌─────────────────────────────┐
│  Gap Analysis               │
│                             │
│         🔍                   │
│  No gaps detected yet.      │
│  Gaps will appear here as   │
│  COMPASS compares your      │
│  implementation against     │
│  the FedRAMP baseline.      │
│                             │
└─────────────────────────────┘
```

#### No OSCAL Output Yet (OSCAL Tab)
```
┌─────────────────────────────┐
│  OSCAL Output               │
│                             │
│         📄                   │
│  OSCAL documents will be    │
│  generated once enough      │
│  controls are mapped.       │
│                             │
│  Progress: 147/325 mapped   │
│  ████████████░░░░░░ 45%     │
│  Need ~80% for SSP gen.     │
│                             │
└─────────────────────────────┘
```

---

## 12. File Structure

```
frontend/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── public/
│   ├── favicon.ico
│   ├── compass-logo.svg
│   └── fonts/
│       ├── Inter-Variable.woff2
│       └── JetBrainsMono-Variable.woff2
│
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                 # Root layout (nav, providers)
│   │   ├── page.tsx                   # Landing page (/)
│   │   ├── globals.css                # Tailwind imports + custom tokens
│   │   ├── dashboard/
│   │   │   └── page.tsx               # Dashboard (/dashboard)
│   │   ├── session/
│   │   │   └── [id]/
│   │   │       ├── page.tsx           # Session view (/session/:id)
│   │   │       └── report/
│   │   │           └── page.tsx       # Export view (/session/:id/report)
│   │   └── auth/
│   │       └── page.tsx               # Auth callback
│   │
│   ├── components/
│   │   ├── ui/                        # Design system primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Chip.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Accordion.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── StatusDot.tsx
│   │   │
│   │   ├── voice/                     # Voice interaction
│   │   │   ├── VoicePanel.tsx         # Mic button, waveform, phase tracker
│   │   │   ├── MicButton.tsx          # Animated microphone button
│   │   │   ├── Waveform.tsx           # Real-time audio visualization
│   │   │   ├── PhaseTracker.tsx       # Vertical step indicator
│   │   │   └── ConnectionStatus.tsx   # WebSocket status indicator
│   │   │
│   │   ├── transcript/                # Conversation transcript
│   │   │   ├── TranscriptPanel.tsx    # Scrollable transcript container
│   │   │   ├── TranscriptEntry.tsx    # Single message bubble
│   │   │   ├── ActionCard.tsx         # Inline action cards (classification, etc.)
│   │   │   ├── StreamingText.tsx      # Typewriter text animation
│   │   │   └── TypingIndicator.tsx    # "COMPASS is listening..." indicator
│   │   │
│   │   ├── context/                   # Right sidebar context panel
│   │   │   ├── ContextPanel.tsx       # Tabbed container
│   │   │   ├── SystemProfileTab.tsx   # System profile display
│   │   │   ├── ClassificationTab.tsx  # FIPS 199 classification display
│   │   │   ├── ControlsTab.tsx        # Control mapping list with families
│   │   │   ├── ControlFamily.tsx      # Accordion for one control family
│   │   │   ├── ControlItem.tsx        # Single control row
│   │   │   ├── GapsTab.tsx            # Gap findings list
│   │   │   ├── GapCard.tsx            # Single gap finding card
│   │   │   ├── OSCALTab.tsx           # OSCAL output viewer
│   │   │   ├── ComplianceDonut.tsx    # Donut chart for compliance score
│   │   │   └── OSCALPreview.tsx       # Syntax-highlighted JSON viewer
│   │   │
│   │   ├── diagram/                   # Architecture diagram features
│   │   │   ├── DiagramUpload.tsx      # Drag-drop upload zone
│   │   │   ├── DiagramViewer.tsx      # Full-screen modal viewer
│   │   │   ├── DiagramAnnotation.tsx  # AI overlay annotation
│   │   │   └── DiagramThumbnail.tsx   # Small preview in profile tab
│   │   │
│   │   ├── dashboard/                 # Dashboard components
│   │   │   ├── StatCards.tsx          # Top stat cards
│   │   │   ├── SessionList.tsx        # Session list table
│   │   │   └── SessionRow.tsx         # Single session row
│   │   │
│   │   ├── layout/                    # Layout components
│   │   │   ├── TopBar.tsx             # Navigation bar
│   │   │   ├── SessionLayout.tsx      # Three-column session layout
│   │   │   └── EventTicker.tsx        # Bottom event ticker bar
│   │   │
│   │   └── landing/                   # Landing page components
│   │       ├── Hero.tsx               # Hero section
│   │       └── ValueProps.tsx         # Three value cards
│   │
│   ├── hooks/
│   │   ├── useLiveAPI.ts             # WebSocket + Gemini Live API management
│   │   ├── useSession.ts             # Firestore session data
│   │   ├── useAudioCapture.ts        # Mic capture → PCM chunks
│   │   ├── useAudioPlayback.ts       # PCM playback via AudioContext
│   │   ├── useAutoScroll.ts          # Smart auto-scroll for transcript
│   │   └── useMediaQuery.ts          # Responsive breakpoint detection
│   │
│   ├── stores/
│   │   ├── sessionStore.ts           # Zustand store for session state
│   │   └── uiStore.ts               # Zustand store for UI preferences (theme, layout)
│   │
│   ├── lib/
│   │   ├── api.ts                    # REST API client (sessions, diagrams, OSCAL)
│   │   ├── audio.ts                  # Audio utilities (PCM conversion, resampling)
│   │   ├── websocket.ts             # WebSocket client with reconnect logic
│   │   ├── auth.ts                   # Firebase Auth integration
│   │   └── formatters.ts            # Display formatters (dates, control IDs, percentages)
│   │
│   └── types/
│       ├── session.ts                # Session, SystemProfile, Classification types
│       ├── controls.ts               # ControlMapping, ControlFamily types
│       ├── gaps.ts                   # GapFinding types
│       ├── oscal.ts                  # OSCAL document types
│       ├── messages.ts               # WebSocket message types
│       └── audio.ts                  # Audio-related types
│
└── __tests__/
    ├── components/
    │   ├── VoicePanel.test.tsx
    │   ├── TranscriptPanel.test.tsx
    │   └── ControlsTab.test.tsx
    ├── hooks/
    │   ├── useLiveAPI.test.ts
    │   └── useAudioCapture.test.ts
    └── stores/
        └── sessionStore.test.ts
```

---

## Appendix A: Key Libraries

| Library | Version | Purpose |
|---|---|---|
| `react` | 19.x | UI framework |
| `next` | 15.x | App framework, routing, SSR |
| `typescript` | 5.x | Type safety |
| `tailwindcss` | 4.x | Utility-first CSS |
| `zustand` | 5.x | Lightweight state management |
| `recharts` | 2.x | Compliance donut chart, progress visualizations |
| `react-syntax-highlighter` | 15.x | OSCAL JSON syntax highlighting |
| `firebase` | 11.x | Auth (Google Sign-In) |
| `framer-motion` | 12.x | Animations (waveform, transitions, diagram annotations) |
| `@tanstack/react-query` | 5.x | REST API data fetching (sessions, OSCAL downloads) |
| `react-dropzone` | 14.x | Diagram file upload |

## Appendix B: Theme Configuration (Tailwind)

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        compass: {
          navy: '#1B2A4A',
          blue: '#2563EB',
          cyan: '#06B6D4',
        },
        surface: {
          bg: 'var(--surface-bg)',
          card: 'var(--surface-card)',
          hover: 'var(--surface-hover)',
          border: 'var(--surface-border)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-mic': 'pulse-mic 1s ease-in-out infinite',
        'glow-blue': 'glow-blue 2s ease-in-out infinite',
        'glow-red': 'glow-red 1.5s ease-in-out infinite',
        'slide-up': 'slide-up 250ms ease-out',
        'slide-in-right': 'slide-in-right 300ms ease-out',
        'fade-in': 'fade-in 200ms ease-out',
      },
      keyframes: {
        'pulse-mic': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.05)', opacity: '0.9' },
        },
        'glow-blue': {
          '0%, 100%': { boxShadow: '0 0 10px rgba(37,99,235,0.3)' },
          '50%': { boxShadow: '0 0 25px rgba(37,99,235,0.6)' },
        },
        'glow-red': {
          '0%, 100%': { boxShadow: '0 0 10px rgba(239,68,68,0.3)' },
          '50%': { boxShadow: '0 0 25px rgba(239,68,68,0.6)' },
        },
        'slide-up': {
          from: { transform: 'translateY(8px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-in-right': {
          from: { transform: 'translateX(16px)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
```

## Appendix C: Audio Processing Notes

### AudioWorklet for Capture
```typescript
// audio-capture-worklet.ts (runs in AudioWorklet thread)
class PCMCaptureProcessor extends AudioWorkletProcessor {
  process(inputs: Float32Array[][], outputs: Float32Array[][], parameters: Record<string, Float32Array>): boolean {
    const input = inputs[0][0]; // Mono channel
    if (input) {
      // Convert float32 [-1,1] to int16 [-32768, 32767]
      const pcm16 = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, Math.round(input[i] * 32767)));
      }
      this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
    }
    return true;
  }
}
```

### Resampling
- Browser AudioContext typically captures at 48kHz
- Gemini Live API expects 16kHz
- Downsample using `OfflineAudioContext` or linear interpolation
- Playback: Gemini outputs 24kHz; upsample to device sample rate via AudioContext

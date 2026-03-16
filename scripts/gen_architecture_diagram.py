"""Generate COMPASS architecture diagram as docs/architecture.png"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

fig, ax = plt.subplots(1, 1, figsize=(22, 14))
ax.set_xlim(0, 22)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('#0a1628')


def draw_box(ax, x, y, w, h, label, sublabel="", color="#1e3a5f", border="#4a90d9", fontsize=9, labelsize=7.5):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                         facecolor=color, edgecolor=border, linewidth=1.8, zorder=2)
    ax.add_patch(box)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 + 0.2, label, ha='center', va='center',
                color='white', fontsize=fontsize, fontweight='bold', zorder=3)
        ax.text(x + w / 2, y + h / 2 - 0.2, sublabel, ha='center', va='center',
                color='#a0c4e8', fontsize=labelsize, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, label, ha='center', va='center',
                color='white', fontsize=fontsize, fontweight='bold', zorder=3)


def draw_group(ax, x, y, w, h, label, color="#0d1e36", border="#4a90d9"):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                         facecolor=color, edgecolor=border, linewidth=2, linestyle='--', zorder=1)
    ax.add_patch(box)
    ax.text(x + 0.25, y + h - 0.28, label, ha='left', va='top',
            color=border, fontsize=9.5, fontweight='bold', zorder=3)


def arrow(ax, x1, y1, x2, y2, label="", color="#4a90d9", bidirectional=False):
    style = "<|-|>" if bidirectional else "-|>"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=1.6), zorder=4)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.05, my + 0.15, label, ha='center', color='#a0c4e8', fontsize=7, zorder=5)


# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(11, 13.55, "COMPASS — System Architecture", ha='center', va='center',
        color='white', fontsize=17, fontweight='bold')
ax.text(11, 13.1, "Compliance Mapping and Policy Assessment Speech System",
        ha='center', va='center', color='#a0c4e8', fontsize=10)

# ── Browser ───────────────────────────────────────────────────────────────────
draw_group(ax, 0.3, 10.8, 5.6, 2.5, "🌐  Browser  (React + TypeScript)", "#1a2e4a", "#4a90d9")
draw_box(ax, 0.55, 11.1, 2.4, 1.8, "Session UI", "Transcript · Controls\nGaps · OSCAL tabs", "#1e3a5f")
draw_box(ax, 3.2, 11.1, 2.4, 1.8, "Web Audio API", "16kHz mic capture\n24kHz PCM playback", "#1e3a5f")

# ── Cloud Run ─────────────────────────────────────────────────────────────────
draw_group(ax, 0.3, 5.8, 5.6, 4.7, "☁️  Google Cloud Run  (FastAPI Backend)", "#0d1e36", "#00b4ff")
draw_box(ax, 0.6, 9.5, 5.0, 0.85, "/ws/live  ·  WebSocket Endpoint", "", "#132840", "#00b4ff", 9)
draw_box(ax, 0.6, 8.4, 5.0, 0.85, "Root Agent  (google-genai Live API)", "", "#132840", "#00b4ff", 9)

# ADK sub-agents
draw_group(ax, 0.5, 5.9, 5.1, 2.3, "Google ADK Sub-agents", "#0a1a30", "#4a90d9")
draw_box(ax, 0.65, 6.1, 1.1, 1.9, "Classifier\nAgent", "FIPS 199\nImpact Scoring", "#162035", "#4a90d9", 7.5, 6.5)
draw_box(ax, 1.85, 6.1, 1.1, 1.9, "Mapper\nAgent", "RAG + Control\nSearch", "#162035", "#4a90d9", 7.5, 6.5)
draw_box(ax, 3.05, 6.1, 1.1, 1.9, "Gap Analyzer\nAgent", "Gap Detection\n+ Remediation", "#162035", "#4a90d9", 7.5, 6.5)
draw_box(ax, 4.25, 6.1, 1.1, 1.9, "OSCAL Gen\nAgent", "SSP / POA&M\nGeneration", "#162035", "#4a90d9", 7.5, 6.5)

# ── Gemini ────────────────────────────────────────────────────────────────────
draw_box(ax, 7.2, 9.0, 4.2, 1.8, "Gemini 2.5 Flash Native Audio",
         "bidiGenerateContent\nInterruptible bidirectional audio", "#0d2137", "#00d4ff", 10.5, 8.5)

# ── GCP Services ──────────────────────────────────────────────────────────────
draw_group(ax, 7.0, 2.5, 8.2, 6.2, "Google Cloud Services", "#0d1e36", "#00b4ff")
draw_box(ax, 7.3, 7.3, 3.5, 1.2, "Vertex AI Vector Search", "NIST 800-53 Rev 5 Embeddings", "#0d2137", "#00b4ff")
draw_box(ax, 11.1, 7.3, 3.8, 1.2, "text-embedding-005", "768-dim control vectors", "#0d2137", "#00b4ff")
draw_box(ax, 7.3, 5.8, 3.5, 1.2, "Cloud Firestore", "Session State + Assessment Data", "#0d2137", "#00b4ff")
draw_box(ax, 11.1, 5.8, 3.8, 1.2, "Cloud Storage (GCS)", "OSCAL Document Artifacts", "#0d2137", "#00b4ff")
draw_box(ax, 8.0, 2.8, 6.0, 1.1,
         "Cloud Run  ·  Cloud Build  ·  Artifact Registry  ·  Terraform IaC",
         "", "#131f33", "#4a90d9", 8)

# ── Knowledge Corpora ─────────────────────────────────────────────────────────
draw_group(ax, 15.5, 5.5, 6.2, 7.6, "Knowledge Corpora", "#0a1628", "#4a90d9")
draw_box(ax, 15.7, 10.7, 5.8, 1.9, "NIST SP 800-53 Rev 5",
         "1,189 controls + enhancements\nFull catalog embedded in Vertex AI", "#162035")
draw_box(ax, 15.7, 8.5, 5.8, 1.9, "FedRAMP Baselines",
         "High (421) · Moderate (325)\nLow (125) · LI-SaaS", "#162035")
draw_box(ax, 15.7, 6.3, 5.8, 1.9, "MITRE ATLAS",
         "AI/ML Threat Techniques\nMapped to mitigating NIST controls", "#162035")

# ── Arrows ────────────────────────────────────────────────────────────────────
# Browser <-> Cloud Run
arrow(ax, 3.1, 10.8, 3.1, 10.35, "PCM audio + JSON events", bidirectional=True)
# WebSocket -> Root Agent
arrow(ax, 3.1, 9.5, 3.1, 9.25)
# Root Agent -> ADK
arrow(ax, 3.1, 8.4, 3.1, 8.0)
# Root Agent <-> Gemini
arrow(ax, 5.6, 8.8, 7.2, 9.5, "bidiGenerateContent", bidirectional=True)
# Gemini -> ADK (function_calls)
arrow(ax, 8.2, 9.0, 3.8, 8.0, "function_calls")
# Mapper -> Vector Search
arrow(ax, 5.6, 6.8, 7.3, 7.8, "", bidirectional=True)
# Vector Search <-> text-embedding
arrow(ax, 10.8, 7.9, 11.1, 7.9, "", bidirectional=True)
# Classifier/Gap -> Firestore
arrow(ax, 5.6, 7.0, 7.3, 6.4)
# OSCAL -> GCS
arrow(ax, 5.6, 6.6, 11.1, 6.2)
# Vector Search -> NIST knowledge
arrow(ax, 14.8, 7.9, 15.7, 11.65)
# Vector Search -> FedRAMP
arrow(ax, 14.8, 7.7, 15.7, 9.45)
# Mapper -> ATLAS
arrow(ax, 5.6, 6.5, 15.7, 7.25)

# ── Save ──────────────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'architecture.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0a1628', edgecolor='none')
print(f"Saved: {os.path.abspath(out_path)}")

"""
Threat Lookup Tool
Maps MITRE ATLAS AI/ML threat techniques to NIST 800-53 mitigating controls.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

_ATLAS_DIR = Path(__file__).parent.parent / "knowledge" / "mitre_atlas"

# Inline ATLAS ↔ 800-53 mapping for common AI/ML threats
# Full corpus loaded from knowledge/mitre_atlas/ at runtime
_INLINE_MAPPINGS: list[dict] = [
    {
        "technique_id": "AML.T0043",
        "technique_name": "Craft Adversarial Data",
        "tactic": "ML Attack Staging",
        "description": "Attackers craft adversarial inputs to cause model misclassification.",
        "mitigating_controls": ["SI-3", "SI-10", "SC-28", "RA-5"],
        "ai_overlay_controls": ["AI-IO-1", "AI-IO-2"],
    },
    {
        "technique_id": "AML.T0048",
        "technique_name": "Backdoor ML Model",
        "tactic": "ML Attack Staging",
        "description": "Embed hidden functionality triggered by specific inputs.",
        "mitigating_controls": ["SA-11", "SA-15", "CM-3", "SI-7"],
        "ai_overlay_controls": ["AI-MOD-1", "AI-MOD-3", "AI-SCRM-1"],
    },
    {
        "technique_id": "AML.T0024",
        "technique_name": "Exfiltration via ML Inference API",
        "tactic": "Exfiltration",
        "description": "Extract training data or model details via inference queries.",
        "mitigating_controls": ["AC-4", "SC-7", "AU-2", "AU-12"],
        "ai_overlay_controls": ["AI-DATA-2", "AI-AUD-1"],
    },
    {
        "technique_id": "AML.T0040",
        "technique_name": "Membership Inference Attack",
        "tactic": "Discovery",
        "description": "Determine if specific data was used to train a model.",
        "mitigating_controls": ["SC-28", "IA-5", "AC-6"],
        "ai_overlay_controls": ["AI-DATA-1", "AI-PROV-1"],
    },
    {
        "technique_id": "AML.T0012",
        "technique_name": "Valid Accounts (ML Pipeline)",
        "tactic": "Initial Access",
        "description": "Use valid credentials to access ML training/serving infrastructure.",
        "mitigating_controls": ["AC-2", "IA-2", "IA-5", "AC-17"],
        "ai_overlay_controls": ["AI-GOV-1"],
    },
    {
        "technique_id": "AML.T0054",
        "technique_name": "LLM Prompt Injection",
        "tactic": "Initial Access",
        "description": "Craft prompts that override LLM system instructions.",
        "mitigating_controls": ["SC-7", "SI-10", "AC-4"],
        "ai_overlay_controls": ["AI-IO-1", "AI-IO-3"],
    },
    {
        "technique_id": "AML.T0031",
        "technique_name": "Erode ML Model Integrity",
        "tactic": "Impact",
        "description": "Poison training data to degrade model performance.",
        "mitigating_controls": ["SI-7", "CM-3", "SA-15"],
        "ai_overlay_controls": ["AI-DATA-1", "AI-DATA-3", "AI-MOD-2"],
    },
]


def _load_atlas_corpus() -> list[dict]:
    """Load full MITRE ATLAS corpus from knowledge directory if available."""
    if not _ATLAS_DIR.exists():
        return _INLINE_MAPPINGS
    mappings = list(_INLINE_MAPPINGS)
    for fp in _ATLAS_DIR.glob("*.json"):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                mappings.extend(data)
            elif isinstance(data, dict):
                mappings.append(data)
        except Exception as exc:
            logger.warning("Failed to load ATLAS file %s: %s", fp, exc)
    return mappings


def threat_lookup_impl(
    query: str | None = None,
    technique_id: str | None = None,
    tactic: str | None = None,
) -> dict:
    """
    Query MITRE ATLAS AI/ML threat mappings to find mitigating controls.

    Args:
        query:        Free-text search (technique name or description).
        technique_id: Specific ATLAS technique ID (e.g. "AML.T0043").
        tactic:       Filter by tactic (e.g. "Exfiltration", "Impact").

    Returns:
        Dict with matching techniques and their mitigating NIST 800-53 controls.
    """
    corpus = _load_atlas_corpus()
    results: list[dict] = []

    if technique_id:
        tid = technique_id.strip().upper()
        results = [t for t in corpus if t.get("technique_id", "").upper() == tid]

    elif tactic:
        tac = tactic.lower()
        results = [t for t in corpus if tac in t.get("tactic", "").lower()]

    elif query:
        q = query.lower()
        results = [
            t for t in corpus
            if q in t.get("technique_name", "").lower()
            or q in t.get("description", "").lower()
            or any(q in c.lower() for c in t.get("mitigating_controls", []))
        ]

    else:
        results = corpus  # Return all if no filter

    return {
        "techniques": results[:20],
        "count": len(results),
        "all_mitigating_controls": sorted({
            c for t in results for c in t.get("mitigating_controls", [])
        }),
    }


threat_lookup_tool = FunctionTool(func=threat_lookup_impl)

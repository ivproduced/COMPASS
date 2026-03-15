"""
FIPS 199 System Classifier
Uses the high-water-mark methodology: overall impact = max(C, I, A).
Combines the hard-coded DATA_TYPE_IMPACT_MAP with NIST SP 800-60 Vol 2 Rev 1
information types loaded from backend/knowledge/nist_800_60/information_types.json.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge" / "nist_800_60"


@lru_cache(maxsize=1)
def _load_800_60() -> dict[str, dict[str, str]]:
    """Load NIST SP 800-60 information types and return as impact map keyed by normalised title."""
    impact_map: dict[str, dict[str, str]] = {}
    fp = _KNOWLEDGE_DIR / "information_types.json"
    if not fp.exists():
        return impact_map
    try:
        with open(fp, encoding="utf-8") as f:
            items = json.load(f)
        for item in items:
            title = item.get("title", "")
            if not title:
                continue
            key = title.upper().replace(" ", "_").replace("-", "_").replace("/", "_")
            impact_map[key] = {
                "confidentiality": item.get("confidentiality", "low"),
                "integrity": item.get("integrity", "low"),
                "availability": item.get("availability", "low"),
            }
            # Also index by 800-60 ID if present (e.g. "C.2.1.1")
            if item.get("id"):
                impact_map[item["id"]] = impact_map[key]
    except Exception as exc:
        logger.warning("Failed to load 800-60 information types: %s", exc)
    return impact_map

# -------------------------------------------------------------------
# Impact lookup table  (FIPS 199 / NIST SP 800-60 Vol 2 Rev 1 basis)
# -------------------------------------------------------------------
DATA_TYPE_IMPACT_MAP: dict[str, dict[str, str]] = {
    # ── PII ──────────────────────────────────────────────────────────
    "PII":                  {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "PII_SSN":              {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PII_FINANCIAL":        {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PII_BIOMETRIC":        {"confidentiality": "high",     "integrity": "high",     "availability": "low"},
    "PII_LOCATION":         {"confidentiality": "moderate", "integrity": "low",      "availability": "low"},
    # ── PHI subtypes (HIPAA / 800-60 C.3.x) ─────────────────────────
    "PHI":                  {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PHI_CLINICAL":         {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PHI_MENTAL_HEALTH":    {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PHI_SUBSTANCE_ABUSE":  {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PHI_GENETIC":          {"confidentiality": "high",     "integrity": "high",     "availability": "low"},
    "PHI_BILLING":          {"confidentiality": "moderate", "integrity": "high",     "availability": "moderate"},
    "PHI_ADMIN":            {"confidentiality": "low",      "integrity": "low",      "availability": "low"},
    # ── CUI ──────────────────────────────────────────────────────────
    "CUI":                  {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "CUI_CONTROLLED":       {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "CUI_EXPORT":           {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "CUI_LEGAL":            {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    # ── Federal / tax / law enforcement ──────────────────────────────
    "FTI":                  {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "CJIS":                 {"confidentiality": "high",     "integrity": "high",     "availability": "high"},
    "LAW_ENFORCEMENT":      {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "NATIONAL_SECURITY":    {"confidentiality": "high",     "integrity": "high",     "availability": "high"},
    # ── Financial ─────────────────────────────────────────────────────
    "FINANCIAL":            {"confidentiality": "moderate", "integrity": "high",     "availability": "moderate"},
    "PAYMENT_CARD":         {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    # ── Credentials / secrets ─────────────────────────────────────────
    "AUTH_CREDENTIALS":     {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "CRYPTOGRAPHIC_KEYS":   {"confidentiality": "high",     "integrity": "high",     "availability": "high"},
    # ── General ───────────────────────────────────────────────────────
    "PROPRIETARY":          {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "TRADE_SECRET":         {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PUBLIC":               {"confidentiality": "low",      "integrity": "low",      "availability": "low"},
    "INTERNAL":             {"confidentiality": "low",      "integrity": "low",      "availability": "low"},
}

IMPACT_RANK: dict[str, int] = {"low": 1, "moderate": 2, "high": 3}
RANK_TO_IMPACT: dict[int, str] = {1: "low", 2: "moderate", 3: "high"}

BASELINE_MAP: dict[int, str] = {
    1: "FedRAMP Low",
    2: "FedRAMP Moderate",
    3: "FedRAMP High",
}
CONTROL_COUNT: dict[int, int] = {1: 156, 2: 325, 3: 421}


def classify_system_impl(
    data_types: list[str],
    system_description: str = "",
    confidentiality_override: str = "",
    integrity_override: str = "",
    availability_override: str = "",
) -> dict:
    """
    Classify a system using FIPS 199 high-water-mark methodology.

    Args:
        data_types: List of data type identifiers (e.g. ["PII", "FTI"]).
        system_description: Optional free-text system description.
        confidentiality_override: Explicit confidentiality level ("low", "moderate", "high").
        integrity_override: Explicit integrity level ("low", "moderate", "high").
        availability_override: Explicit availability level ("low", "moderate", "high").

    Returns:
        Dict with fips_199_classification, fedramp_baseline, control_count.
    """
    max_c, max_i, max_a = 1, 1, 1

    matched: list[str] = []
    unrecognized: list[str] = []
    sp800_60 = _load_800_60()

    for dt in data_types:
        key = dt.upper().replace(" ", "_").replace("-", "_").replace("/", "_")
        impacts = DATA_TYPE_IMPACT_MAP.get(key) or sp800_60.get(key)
        if impacts:
            max_c = max(max_c, IMPACT_RANK[impacts["confidentiality"]])
            max_i = max(max_i, IMPACT_RANK[impacts["integrity"]])
            max_a = max(max_a, IMPACT_RANK[impacts["availability"]])
            matched.append(dt)
        else:
            unrecognized.append(dt)

    # Apply explicit CIA overrides — these represent the system owner's stated
    # impact levels, which take precedence over the data-type high-water mark.
    if confidentiality_override.lower() in IMPACT_RANK:
        max_c = IMPACT_RANK[confidentiality_override.lower()]
    if integrity_override.lower() in IMPACT_RANK:
        max_i = IMPACT_RANK[integrity_override.lower()]
    if availability_override.lower() in IMPACT_RANK:
        max_a = IMPACT_RANK[availability_override.lower()]

    overall = max(max_c, max_i, max_a)

    return {
        "fips_199_classification": {
            "confidentiality": RANK_TO_IMPACT[max_c],
            "integrity":       RANK_TO_IMPACT[max_i],
            "availability":    RANK_TO_IMPACT[max_a],
            "overall":         RANK_TO_IMPACT[overall],
        },
        "fedramp_baseline":      BASELINE_MAP[overall],
        "control_count":         CONTROL_COUNT[overall],
        "data_types_analyzed":   data_types,
        "data_types_matched":    matched,
        "data_types_unrecognized": unrecognized,
        "rationale": (
            f"High-water-mark driven by confidentiality={RANK_TO_IMPACT[max_c]}, "
            f"integrity={RANK_TO_IMPACT[max_i]}, availability={RANK_TO_IMPACT[max_a]}."
        ),
    }


classify_system_tool = FunctionTool(func=classify_system_impl)

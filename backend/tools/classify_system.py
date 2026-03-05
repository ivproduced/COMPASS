"""
FIPS 199 System Classifier
Uses the high-water-mark methodology: overall impact = max(C, I, A).
Ported from sia_logic_core.py ImpactEngine.
"""
from __future__ import annotations

from google.adk.tools import FunctionTool

# -------------------------------------------------------------------
# Impact lookup table
# -------------------------------------------------------------------
DATA_TYPE_IMPACT_MAP: dict[str, dict[str, str]] = {
    "PII":              {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "PII_SSN":          {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PII_FINANCIAL":    {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PHI":              {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "CUI":              {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"},
    "CUI_CONTROLLED":   {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "FTI":              {"confidentiality": "high",     "integrity": "high",     "availability": "high"},
    "FINANCIAL":        {"confidentiality": "moderate", "integrity": "high",     "availability": "moderate"},
    "AUTH_CREDENTIALS": {"confidentiality": "high",     "integrity": "high",     "availability": "moderate"},
    "PUBLIC":           {"confidentiality": "low",      "integrity": "low",      "availability": "low"},
    "INTERNAL":         {"confidentiality": "low",      "integrity": "low",      "availability": "low"},
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
) -> dict:
    """
    Classify a system using FIPS 199 high-water-mark methodology.

    Args:
        data_types: List of data type identifiers (e.g. ["PII", "FTI"]).
        system_description: Optional free-text system description.

    Returns:
        Dict with fips_199_classification, fedramp_baseline, control_count.
    """
    max_c, max_i, max_a = 1, 1, 1

    matched: list[str] = []
    unrecognized: list[str] = []

    for dt in data_types:
        key = dt.upper().replace(" ", "_").replace("-", "_")
        if key in DATA_TYPE_IMPACT_MAP:
            impacts = DATA_TYPE_IMPACT_MAP[key]
            max_c = max(max_c, IMPACT_RANK[impacts["confidentiality"]])
            max_i = max(max_i, IMPACT_RANK[impacts["integrity"]])
            max_a = max(max_a, IMPACT_RANK[impacts["availability"]])
            matched.append(dt)
        else:
            unrecognized.append(dt)

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

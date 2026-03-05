"""
Data Type Mapper
Maps free-text data type descriptions to canonical tags and C/I/A impact levels.
"""
from __future__ import annotations

from google.adk.tools import FunctionTool

from .classify_system import DATA_TYPE_IMPACT_MAP, classify_system_impl

# Alias expansions: common phrases → canonical tag
_ALIASES: dict[str, str] = {
    "personally identifiable information": "PII",
    "social security number": "PII_SSN",
    "ssn": "PII_SSN",
    "protected health information": "PHI",
    "health data": "PHI",
    "medical records": "PHI",
    "controlled unclassified information": "CUI",
    "federal tax information": "FTI",
    "tax information": "FTI",
    "financial records": "PII_FINANCIAL",
    "financial data": "PII_FINANCIAL",
    "credentials": "AUTH_CREDENTIALS",
    "passwords": "AUTH_CREDENTIALS",
    "authentication data": "AUTH_CREDENTIALS",
    "public": "PUBLIC",
    "internal": "INTERNAL",
}


def map_data_types_impl(descriptions: list[str]) -> dict:
    """
    Map free-text data type descriptions to canonical tags and impact levels.

    Args:
        descriptions: List of free-text descriptions (e.g. ["social security numbers", "medical records"]).

    Returns:
        Dict with canonical_tags, impact_map, and classification.
    """
    canonical: list[str] = []
    mapping_detail: list[dict] = []

    for desc in descriptions:
        lower = desc.strip().lower()
        tag = _ALIASES.get(lower, desc.upper().replace(" ", "_").replace("-", "_"))
        canonical.append(tag)
        impacts = DATA_TYPE_IMPACT_MAP.get(tag, {"confidentiality": "moderate", "integrity": "moderate", "availability": "low"})
        mapping_detail.append({"input": desc, "canonical_tag": tag, "impacts": impacts})

    classification = classify_system_impl(data_types=canonical)

    return {
        "canonical_tags": canonical,
        "mapping_detail": mapping_detail,
        "classification": classification,
    }


map_data_types_tool = FunctionTool(func=map_data_types_impl)

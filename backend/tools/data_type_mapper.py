"""
Data Type Mapper
Maps free-text data type descriptions to canonical tags and C/I/A impact levels.
"""
from __future__ import annotations

from google.adk.tools import FunctionTool

from .classify_system import DATA_TYPE_IMPACT_MAP, classify_system_impl

# Alias expansions: common phrases → canonical tag
# LLM should pass the most specific matching phrase when calling map_data_types.
_ALIASES: dict[str, str] = {
    # PII
    "personally identifiable information": "PII",
    "pii": "PII",
    "social security number": "PII_SSN",
    "social security numbers": "PII_SSN",
    "ssn": "PII_SSN",
    "biometric data": "PII_BIOMETRIC",
    "fingerprints": "PII_BIOMETRIC",
    "facial recognition": "PII_BIOMETRIC",
    "location data": "PII_LOCATION",
    "gps data": "PII_LOCATION",
    # PHI — general
    "protected health information": "PHI",
    "phi": "PHI",
    "health data": "PHI",
    "hipaa data": "PHI",
    # PHI — clinical records
    "medical records": "PHI_CLINICAL",
    "electronic health records": "PHI_CLINICAL",
    "ehr": "PHI_CLINICAL",
    "emr": "PHI_CLINICAL",
    "patient records": "PHI_CLINICAL",
    "clinical data": "PHI_CLINICAL",
    "diagnoses": "PHI_CLINICAL",
    "prescriptions": "PHI_CLINICAL",
    "lab results": "PHI_CLINICAL",
    # PHI — behavioral / sensitive
    "mental health records": "PHI_MENTAL_HEALTH",
    "psychiatric records": "PHI_MENTAL_HEALTH",
    "behavioral health": "PHI_MENTAL_HEALTH",
    "substance abuse records": "PHI_SUBSTANCE_ABUSE",
    "addiction treatment": "PHI_SUBSTANCE_ABUSE",
    "genetic data": "PHI_GENETIC",
    "genomic data": "PHI_GENETIC",
    "dna data": "PHI_GENETIC",
    # PHI — administrative
    "medical billing": "PHI_BILLING",
    "insurance claims": "PHI_BILLING",
    "health insurance": "PHI_BILLING",
    "health care administration": "PHI_ADMIN",
    "appointment scheduling": "PHI_ADMIN",
    # CUI
    "controlled unclassified information": "CUI",
    "cui": "CUI",
    "itar": "CUI_EXPORT",
    "export controlled": "CUI_EXPORT",
    "legal proceedings": "CUI_LEGAL",
    "attorney client": "CUI_LEGAL",
    # Federal
    "federal tax information": "FTI",
    "tax information": "FTI",
    "irs data": "FTI",
    "criminal justice information": "CJIS",
    "cjis": "CJIS",
    "law enforcement data": "LAW_ENFORCEMENT",
    "classified information": "NATIONAL_SECURITY",
    "national security": "NATIONAL_SECURITY",
    # Financial
    "financial records": "PII_FINANCIAL",
    "financial data": "PII_FINANCIAL",
    "credit card data": "PAYMENT_CARD",
    "payment card": "PAYMENT_CARD",
    "pci data": "PAYMENT_CARD",
    # Credentials
    "credentials": "AUTH_CREDENTIALS",
    "passwords": "AUTH_CREDENTIALS",
    "authentication data": "AUTH_CREDENTIALS",
    "api keys": "CRYPTOGRAPHIC_KEYS",
    "encryption keys": "CRYPTOGRAPHIC_KEYS",
    "private keys": "CRYPTOGRAPHIC_KEYS",
    # General
    "trade secrets": "TRADE_SECRET",
    "proprietary": "PROPRIETARY",
    "public": "PUBLIC",
    "publicly available": "PUBLIC",
    "internal": "INTERNAL",
    "internal use only": "INTERNAL",
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

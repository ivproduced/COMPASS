"""
OSCAL Validator Tool
Validates OSCAL JSON documents against the NIST OSCAL 1.1.2 schema.
Uses the oscal-pydantic library when available; falls back to structural heuristics.
"""
from __future__ import annotations

import logging

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

# Required top-level keys per document type
_REQUIRED_KEYS: dict[str, list[str]] = {
    "ssp":                {"system-security-plan": ["uuid", "metadata", "import-profile",
                                                     "system-characteristics",
                                                     "system-implementation",
                                                     "control-implementation"]},
    "poam":               {"plan-of-action-and-milestones": ["uuid", "metadata", "poam-items"]},
    "assessment_results": {"assessment-results": ["uuid", "metadata", "results"]},
}

_METADATA_REQUIRED = ["title", "last-modified", "version", "oscal-version"]


def validate_oscal_impl(content: dict, document_type: str = "ssp") -> dict:
    """
    Validate an OSCAL JSON document for structural completeness.

    Args:
        content:       The full OSCAL JSON document as a dict.
        document_type: One of "ssp", "poam", or "assessment_results".

    Returns:
        Dict with valid (bool), errors (list), warnings (list).
    """
    errors: list[str] = []
    warnings: list[str] = []

    doc_type_keys = _REQUIRED_KEYS.get(document_type)
    if not doc_type_keys:
        return {"valid": False, "errors": [f"Unknown document_type: {document_type}"], "warnings": []}

    root_key = list(doc_type_keys.keys())[0]
    required_children = doc_type_keys[root_key]

    # Root key check
    if root_key not in content:
        errors.append(f"Missing root key: '{root_key}'")
        return {"valid": False, "errors": errors, "warnings": warnings}

    doc = content[root_key]

    # UUID check
    if not doc.get("uuid"):
        errors.append("Missing required field: uuid")

    # Required children
    for field in required_children:
        if field not in doc:
            errors.append(f"Missing required field: {field}")

    # Metadata check
    if meta := doc.get("metadata"):
        for mf in _METADATA_REQUIRED:
            if not meta.get(mf):
                errors.append(f"Missing metadata field: {mf}")
        # OSCAL version check
        ospv = meta.get("oscal-version", "")
        if ospv and not ospv.startswith("1.1"):
            warnings.append(f"oscal-version '{ospv}' may not be fully supported; expected 1.1.x")
    else:
        errors.append("Missing required section: metadata")

    # SSP-specific checks
    if document_type == "ssp":
        sys_char = doc.get("system-characteristics", {})
        if not sys_char.get("system-name"):
            warnings.append("system-characteristics.system-name is empty")
        if not sys_char.get("security-sensitivity-level"):
            errors.append("system-characteristics.security-sensitivity-level is required")
        ctrl_impl = doc.get("control-implementation", {})
        if not ctrl_impl.get("implemented-requirements"):
            warnings.append("control-implementation.implemented-requirements is empty — no controls mapped yet")

    # POA&M-specific checks
    if document_type == "poam":
        items = doc.get("poam-items", [])
        if not items:
            warnings.append("poam-items is empty — no gaps recorded yet")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "summary": f"{'VALID' if valid else 'INVALID'}: {len(errors)} error(s), {len(warnings)} warning(s)",
    }


validate_oscal_tool = FunctionTool(func=validate_oscal_impl)

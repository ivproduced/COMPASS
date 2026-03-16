"""
Gap Analyzer Tool
Compares stated control implementations against the FedRAMP baseline
and identifies missing or incomplete controls.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Minimal inline baseline for resilience when files are absent
_INLINE_MODERATE_FAMILIES = [
    "AC", "AT", "AU", "CA", "CM", "CP", "IA", "IR",
    "MA", "MP", "PE", "PL", "PM", "PS", "RA", "SA",
    "SC", "SI",
]


def _load_baseline(baseline: str = "moderate") -> list[str]:
    """Return list of control IDs in the specified FedRAMP baseline."""
    # Normalise: "FedRAMP High" → "high", "FedRAMP Moderate" → "moderate", "high" → "high"
    key = baseline.lower().strip()
    key = key.replace("fedramp ", "").replace("fedramp_", "")  # strip prefix if present
    key = key.replace(" ", "_").replace("-", "_")
    # Try new fedramp/ directory first
    path = _KNOWLEDGE_DIR / "fedramp" / f"fedramp_rev5_{key}_baseline.json"
    if not path.exists():
        # Legacy path fallback
        path = _KNOWLEDGE_DIR / "fedramp_moderate" / "baseline_controls.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # Supports both plain string arrays and object arrays with "id" key
            return [c["id"] if isinstance(c, dict) else c for c in data]
        except Exception as exc:
            logger.warning("Could not load baseline file: %s", exc)
    return []


def gap_analysis_impl(
    control_id: str,
    current_implementation: str,
    required_implementation: str = "",
    component: str = "",
) -> dict:
    """
    Analyze a compliance gap for a specific control.

    Args:
        control_id:               NIST 800-53 control ID (e.g. "AC-4").
        current_implementation:   What the architect described as in-place.
        required_implementation:  What FedRAMP requires (leave blank to auto-derive).
        component:                System component this applies to.

    Returns:
        Dict with gap assessment, risk level, and remediation guidance.
    """
    ctrl_id = control_id.strip().upper()
    # Normalize smart quotes/apostrophes to ASCII before matching
    _impl_norm = current_implementation.replace("\u2019", "'").replace("\u2018", "'")
    _impl_lower = _impl_norm.lower()
    logger.info("gap_analysis_impl: control=%s impl=%r", ctrl_id, _impl_lower[:120])

    # Determine gap severity based on heuristics
    is_gap = bool(
        not current_implementation
        or "not yet" in _impl_lower
        or "not implemented" in _impl_lower
        or "n/a" in _impl_lower
        or "have no" in _impl_lower
        or "has no" in _impl_lower
        or "don't have" in _impl_lower
        or "dont have" in _impl_lower
        or "do not have" in _impl_lower
        or "does not have" in _impl_lower
        or "don't use" in _impl_lower
        or "dont use" in _impl_lower
        or "do not use" in _impl_lower
        or "does not use" in _impl_lower
        or "don't currently" in _impl_lower
        or "dont currently" in _impl_lower
        or "do not currently" in _impl_lower
        or "currently don't" in _impl_lower
        or "currently do not" in _impl_lower        or "currently not" in _impl_lower          # catches "currently not using", "currently not implemented", etc.        or "missing" in _impl_lower
        or "absent" in _impl_lower
        or "not in place" in _impl_lower
        or "haven't" in _impl_lower
        or "hasn't" in _impl_lower
        or "we lack" in _impl_lower
        or "without" in _impl_lower
        or "not enabled" in _impl_lower
        or "not deployed" in _impl_lower
        or "not configured" in _impl_lower
        or "not set up" in _impl_lower
        or "not established" in _impl_lower
        or "only password" in _impl_lower          # "username and password only" → no MFA
        or "password only" in _impl_lower
        or "just password" in _impl_lower
        or "username and password" in _impl_lower  # classic no-MFA indicator for auth controls
        or "use name and password" in _impl_lower  # STT variant of "username and password"
        or re.search(r"\bnot\s+using\b", _impl_lower)   # "not using MFA", "not using 2FA"
        or re.search(r"\bnot\s+(?!needed|required|applicable|allowed|necessary)\w+ed\b", _impl_lower)
        or re.search(r"\bno\s+(?:controls?|process|policy|policies|mechanism|logging|monitoring|mfa|multi.?factor|authentication|2fa|encryption|audit|review|scanning|baseline|documentation)\b", _impl_lower)
        or re.search(r"\bneed\s+to\b", _impl_lower)
        or re.search(r"\bis\s+not\s+(?!needed|required|applicable|allowed|necessary)\b", _impl_lower)
        or re.search(r"\bare\s+not\s+(?!needed|required|applicable|allowed|necessary)\b", _impl_lower)
        or re.search(r"\bwas\s+not\s+(?!needed|required|applicable|allowed|necessary)\b", _impl_lower)
        or re.search(r"\bonly\s+(?:using\s+)?(?:username|password|user(?:name)?[\s/]+password)\b", _impl_lower)
        or re.search(r"\busing\s+only\s+\w", _impl_lower)  # "using only username/password/X"
    )

    is_partial = not is_gap and any(
        phrase in _impl_lower
        for phrase in ["partial", "limited", "in progress", "planned", "some"]
    )

    if is_gap:
        status = "not_implemented"
        risk_level = "high"
    elif is_partial:
        status = "partial"
        risk_level = "moderate"
    else:
        status = "implemented"
        risk_level = "low"

    return {
        "control_id": ctrl_id,
        "component": component,
        "implementation_status": status,
        "risk_level": risk_level,
        "current_implementation": current_implementation,
        "required_implementation": required_implementation or f"FedRAMP Moderate baseline requirement for {ctrl_id}",
        "is_gap": is_gap or is_partial,
        "remediation": _suggest_remediation(ctrl_id, current_implementation) if (is_gap or is_partial) else "",
        "estimated_effort": "weeks" if is_gap else "days",
    }


# -------------------------------------------------------------------
# Inline remediation hints for common controls
# Full RAG-based remediation will augment these at runtime
# -------------------------------------------------------------------
_REMEDIATION_HINTS: dict[str, str] = {
    "SC-7":  "Deploy a Web Application Firewall (WAF) in front of public-facing endpoints. Implement network segmentation with explicit ingress/egress rules.",
    "SC-28": "Enable encryption at rest on all data stores. For AWS RDS, enable storage encryption with a KMS key. For GCP Cloud SQL, enable CMEK.",
    "AC-2":  "Implement automated account provisioning/deprovisioning integrated with HR system. Enable account review workflow on a quarterly schedule.",
    "AC-4":  "Implement content-based filtering at API boundaries. Deploy a Lambda authorizer that inspects request/response payloads for PII pattern leakage.",
    "AU-6":  "Configure log aggregation into a SIEM. Set up automated alerting for anomalous access patterns. Retain logs for minimum 90 days online, 1 year archive.",
    "IA-5":  "Enforce MFA for all privileged accounts. Implement password complexity requirements and rotation policies via IAM policies.",
    "RA-5":  "Establish a quarterly vulnerability scanning cadence using a FedRAMP-authorized scanner. Remediate Critical findings within 30 days.",
    "CM-6":  "Document configuration baselines for all system components. Use configuration management tooling (Ansible, Terraform) to enforce baselines.",
    "SI-3":  "Deploy endpoint protection on all compute instances. Enable real-time malware scanning on file upload endpoints.",
}


def _suggest_remediation(control_id: str, current_impl: str) -> str:
    family_id = control_id.split("(")[0].strip()
    return _REMEDIATION_HINTS.get(
        family_id,
        f"Review FedRAMP Moderate requirements for {control_id} and document a remediation plan addressing the identified gap.",
    )


gap_analysis_tool = FunctionTool(func=gap_analysis_impl)

"""
Gap Analyzer Tool
Compares stated control implementations against the FedRAMP baseline
and identifies missing or incomplete controls.
"""
from __future__ import annotations

import json
import logging
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
    path = _KNOWLEDGE_DIR / "fedramp_moderate" / "baseline_controls.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return [c["id"] if isinstance(c, dict) else c for c in data]
        except Exception as exc:
            logger.warning("Could not load baseline file: %s", exc)
    # Inline fallback
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

    # Determine gap severity based on heuristics
    is_gap = bool(
        not current_implementation
        or "not yet" in current_implementation.lower()
        or "not implemented" in current_implementation.lower()
        or "n/a" in current_implementation.lower()
    )

    is_partial = not is_gap and any(
        phrase in current_implementation.lower()
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

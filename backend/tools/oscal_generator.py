"""
OSCAL Generator Tool
Builds OSCAL-formatted SSP and POA&M JSON documents from assessment state.
Conforms to NIST OSCAL 1.1.2.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_oscal_impl(
    document_type: str,
    system_name: str = "",
    system_description: str = "",
    fips_199_level: str = "moderate",
    control_mappings: list[dict] | None = None,
    gap_findings: list[dict] | None = None,
    data_types: list[dict] | None = None,
    boundary_description: str = "",
) -> dict:
    """
    Generate an OSCAL-formatted document from assessment findings.

    Args:
        document_type:        "ssp", "poam", or "assessment_results".
        system_name:          Name of the system under assessment.
        system_description:   Brief description of the system.
        fips_199_level:       Overall FIPS 199 impact level (low/moderate/high).
        control_mappings:     List of control mapping dicts from the session.
        gap_findings:         List of gap finding dicts from the session.
        data_types:           List of information type dicts with C/I/A impacts.
        boundary_description: Authorization boundary description.

    Returns:
        Dict with document_type, uuid, and the full OSCAL JSON content.
    """
    control_mappings = control_mappings or []
    gap_findings = gap_findings or []
    data_types = data_types or []
    doc_uuid = str(uuid.uuid4())

    if document_type == "ssp":
        content = _build_ssp(
            doc_uuid, system_name, system_description,
            fips_199_level, control_mappings, data_types,
            boundary_description,
        )
    elif document_type == "poam":
        content = _build_poam(doc_uuid, system_name, gap_findings)
    elif document_type == "assessment_results":
        content = _build_assessment_results(doc_uuid, system_name, control_mappings, gap_findings)
    else:
        return {"error": f"Unknown document_type: {document_type}"}

    return {
        "document_type": document_type,
        "uuid": doc_uuid,
        "oscal_version": "1.1.2",
        "generated_at": _utcnow(),
        "content": content,
    }


# -------------------------------------------------------------------
# Internal builders
# -------------------------------------------------------------------

def _build_ssp(
    doc_uuid: str,
    system_name: str,
    description: str,
    fips_199_level: str,
    mappings: list[dict],
    data_types: list[dict],
    boundary: str,
) -> dict:
    return {
        "system-security-plan": {
            "uuid": doc_uuid,
            "metadata": {
                "title": f"System Security Plan — {system_name}",
                "last-modified": _utcnow(),
                "version": "1.0.0",
                "oscal-version": "1.1.2",
                "roles": [
                    {"id": "system-owner", "title": "System Owner"},
                    {"id": "authorizing-official", "title": "Authorizing Official"},
                    {"id": "compass-agent", "title": "COMPASS AI Assessment Agent"},
                ],
                "parties": [
                    {
                        "uuid": str(uuid.uuid4()),
                        "type": "tool",
                        "name": "COMPASS",
                        "remarks": "FedRAMP Compliance Voice Agent — AI-generated SSP",
                    }
                ],
            },
            "import-profile": {"href": "#fedramp-moderate-baseline"},
            "system-characteristics": {
                "system-id": str(uuid.uuid4()),
                "system-name": system_name,
                "description": description,
                "security-sensitivity-level": fips_199_level,
                "system-information": {
                    "information-types": [
                        {
                            "uuid": str(uuid.uuid4()),
                            "title": dt.get("title", "Information Type"),
                            "description": dt.get("description", ""),
                            "confidentiality-impact": {"base": dt.get("confidentiality", "moderate")},
                            "integrity-impact":       {"base": dt.get("integrity", "moderate")},
                            "availability-impact":    {"base": dt.get("availability", "low")},
                        }
                        for dt in data_types
                    ]
                },
                "security-impact-level": {
                    "security-objective-confidentiality": fips_199_level,
                    "security-objective-integrity":       fips_199_level,
                    "security-objective-availability":    fips_199_level,
                },
                "authorization-boundary": {"description": boundary},
            },
            "system-implementation": {
                "users": [
                    {
                        "uuid": str(uuid.uuid4()),
                        "title": "Security Architect",
                        "role-ids": ["system-owner"],
                    }
                ],
                "components": [],
            },
            "control-implementation": {
                "description": "Control implementations identified by COMPASS voice assessment.",
                "implemented-requirements": [
                    {
                        "uuid": str(uuid.uuid4()),
                        "control-id": m.get("control_id", "").lower(),
                        "props": [
                            {
                                "name": "implementation-status",
                                "ns": "https://fedramp.gov/ns/oscal",
                                "value": m.get("implementation_status", "planned"),
                            }
                        ],
                        "statements": [
                            {
                                "statement-id": f"{m.get('control_id', '').lower()}_smt",
                                "uuid": str(uuid.uuid4()),
                                "description": m.get("implementation_description", ""),
                            }
                        ],
                    }
                    for m in mappings
                ],
            },
        }
    }


def _build_poam(doc_uuid: str, system_name: str, gaps: list[dict]) -> dict:
    return {
        "plan-of-action-and-milestones": {
            "uuid": doc_uuid,
            "metadata": {
                "title": f"Plan of Action & Milestones — {system_name}",
                "last-modified": _utcnow(),
                "version": "1.0.0",
                "oscal-version": "1.1.2",
            },
            "poam-items": [
                {
                    "uuid": str(uuid.uuid4()),
                    "title": f"Gap: {g.get('control_id', '')} — {g.get('gap_title', '')}",
                    "description": g.get("gap_description", ""),
                    "props": [
                        {"name": "risk-level", "value": g.get("risk_level", "moderate")}
                    ],
                    "related-observations": [
                        {"description": g.get("gap_description", "")}
                    ],
                    "associated-risks": [
                        {
                            "uuid": str(uuid.uuid4()),
                            "title": f"Risk: {g.get('control_id','')}",
                            "description": g.get("risk_description", ""),
                            "status": "open",
                        }
                    ],
                    "remediation-tracking": {
                        "required-adjustments": g.get("remediation", ""),
                        "remarks": f"Estimated effort: {g.get('estimated_effort', 'weeks')}",
                    },
                }
                for g in gaps
            ],
        }
    }


def _build_assessment_results(
    doc_uuid: str,
    system_name: str,
    mappings: list[dict],
    gaps: list[dict],
) -> dict:
    total = len(mappings)
    impl = sum(1 for m in mappings if m.get("implementation_status") == "implemented")
    return {
        "assessment-results": {
            "uuid": doc_uuid,
            "metadata": {
                "title": f"Assessment Results — {system_name}",
                "last-modified": _utcnow(),
                "version": "1.0.0",
                "oscal-version": "1.1.2",
            },
            "results": [
                {
                    "uuid": str(uuid.uuid4()),
                    "title": "COMPASS Voice Assessment",
                    "description": f"Automated assessment via COMPASS voice agent. {impl}/{total} controls assessed.",
                    "start": _utcnow(),
                    "reviewed-controls": {
                        "control-selections": [
                            {"description": "All FedRAMP Moderate baseline controls"}
                        ]
                    },
                    "findings": [
                        {
                            "uuid": str(uuid.uuid4()),
                            "title": f"Gap: {g.get('control_id','')}",
                            "description": g.get("gap_description", ""),
                            "target": {
                                "type": "objective-id",
                                "target-id": g.get("control_id", "").lower(),
                                "status": {"state": "not-satisfied"},
                            },
                        }
                        for g in gaps
                    ],
                }
            ],
        }
    }


generate_oscal_tool = FunctionTool(func=generate_oscal_impl)

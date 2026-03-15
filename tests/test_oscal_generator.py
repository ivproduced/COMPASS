"""
test_oscal_generator.py — Unit tests for OSCAL generation and validation
"""
import uuid
import pytest

from backend.tools.oscal_generator import generate_oscal_impl
from backend.tools.oscal_validator import validate_oscal_impl


SAMPLE_MAPPINGS = [
    {
        "control_id": "AC-2",
        "title": "Account Management",
        "family": "AC",
        "implementation_status": "implemented",
        "confidence_score": 0.9,
        "component_refs": ["IAM"],
    },
    {
        "control_id": "SC-7",
        "title": "Boundary Protection",
        "family": "SC",
        "implementation_status": "partial",
        "confidence_score": 0.7,
        "component_refs": ["WAF"],
    },
    {
        "control_id": "AU-6",
        "title": "Audit Record Review",
        "family": "AU",
        "implementation_status": "not_implemented",
        "confidence_score": 0.0,
        "component_refs": [],
    },
]

SAMPLE_GAPS = [
    {
        "control_id": "AU-6",
        "gap_title": "Missing audit logging",
        "gap_description": "No automated audit review configured.",
        "risk_level": "high",
        "remediation": "Enable CloudWatch and configure automated analysis.",
        "estimated_effort": "weeks",
    }
]


class TestOSCALGenerator:

    def test_ssp_generation_keys(self):
        """SSP output must contain required top-level OSCAL keys."""
        result = generate_oscal_impl(
            document_type="ssp",
            system_name="Test System",
            fips_199_level="Moderate",
            control_mappings=SAMPLE_MAPPINGS,
            gap_findings=[],
        )
        assert result.get("document_type") == "ssp"
        assert "uuid" in result
        content = result.get("content", {})
        assert "system-security-plan" in content
        ssp = content["system-security-plan"]
        assert "metadata" in ssp
        assert "system-characteristics" in ssp
        assert "control-implementation" in ssp

    def test_poam_generation_keys(self):
        """POA&M output must include poam-items."""
        result = generate_oscal_impl(
            document_type="poam",
            system_name="Test System",
            fips_199_level="Moderate",
            control_mappings=SAMPLE_MAPPINGS,
            gap_findings=SAMPLE_GAPS,
        )
        assert result.get("document_type") == "poam"
        content = result.get("content", {})
        assert "plan-of-action-and-milestones" in content
        poam = content["plan-of-action-and-milestones"]
        assert "poam-items" in poam
        assert len(poam["poam-items"]) == len(SAMPLE_GAPS)

    def test_assessment_results_generation(self):
        """Assessment results must include findings."""
        result = generate_oscal_impl(
            document_type="assessment_results",
            system_name="Test System",
            fips_199_level="Moderate",
            control_mappings=SAMPLE_MAPPINGS,
            gap_findings=SAMPLE_GAPS,
        )
        assert result.get("document_type") == "assessment_results"
        content = result.get("content", {})
        assert "assessment-results" in content

    def test_uuid_is_valid(self):
        """Generated document UUID must be a valid UUID4."""
        result = generate_oscal_impl(
            document_type="ssp",
            system_name="Test",
            fips_199_level="Low",
            control_mappings=[],
            gap_findings=[],
        )
        uuid_str = result.get("uuid", "")
        # Should not raise
        parsed = uuid.UUID(uuid_str)
        assert parsed.version == 4

    def test_oscal_version_in_metadata(self):
        """OSCAL version must be 1.1.2."""
        result = generate_oscal_impl(
            document_type="ssp",
            system_name="Test",
            fips_199_level="Low",
            control_mappings=[],
            gap_findings=[],
        )
        ssp = result["content"]["system-security-plan"]
        assert ssp["metadata"]["oscal-version"] == "1.1.2"

    def test_control_implementations_populated(self):
        """Implemented controls should appear in control-implementation."""
        result = generate_oscal_impl(
            document_type="ssp",
            system_name="Test",
            fips_199_level="Moderate",
            control_mappings=SAMPLE_MAPPINGS,
            gap_findings=[],
        )
        ssp = result["content"]["system-security-plan"]
        impls = ssp["control-implementation"].get("implemented-requirements", [])
        control_ids = [i["control-id"] for i in impls]
        # OSCAL standard uses lowercase control IDs (e.g. "ac-2")
        assert "ac-2" in control_ids
        assert "sc-7" in control_ids


class TestOSCALValidator:

    def test_valid_ssp_passes(self):
        """A well-formed SSP should pass validation."""
        result = generate_oscal_impl(
            document_type="ssp",
            system_name="ValidTest",
            fips_199_level="Moderate",
            control_mappings=SAMPLE_MAPPINGS,
            gap_findings=[],
        )
        validation = validate_oscal_impl(
            content=result["content"],
            document_type="ssp",
        )
        assert validation["valid"] is True
        assert len(validation.get("errors", [])) == 0

    def test_empty_content_fails(self):
        """Empty content dict should fail validation with errors."""
        validation = validate_oscal_impl(content={}, document_type="ssp")
        assert validation["valid"] is False
        assert len(validation.get("errors", [])) > 0

    def test_poam_with_no_items_warns(self):
        """POA&M with empty poam-items should produce a warning."""
        minimal_poam = {
            "plan-of-action-and-milestones": {
                "uuid": str(uuid.uuid4()),
                "metadata": {
                    "title": "Test",
                    "last-modified": "2025-01-01T00:00:00Z",
                    "oscal-version": "1.1.2",
                },
                "poam-items": [],
            }
        }
        validation = validate_oscal_impl(content=minimal_poam, document_type="poam")
        warnings = validation.get("warnings", [])
        assert any("poam-items" in w.lower() or "empty" in w.lower() for w in warnings)

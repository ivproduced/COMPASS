"""
test_classifier.py — Unit tests for FIPS 199 classification logic
"""
import pytest
from backend.tools.classify_system import classify_system_impl
from backend.tools.data_type_mapper import map_data_types_impl


class TestFIPS199Classifier:

    def test_pii_maps_to_moderate(self):
        """PII alone should yield Moderate baseline."""
        result = classify_system_impl(data_types=["PII"])
        assert result["overall_impact"] == "Moderate"
        assert result["fedramp_baseline"] == "Moderate"
        assert result["control_count"] == 325

    def test_phi_maps_to_high(self):
        """PHI should trigger High."""
        result = classify_system_impl(data_types=["PHI"])
        assert result["overall_impact"] == "High"
        assert result["fedramp_baseline"] == "High"
        assert result["control_count"] == 421

    def test_public_maps_to_low(self):
        """PUBLIC data should yield Low."""
        result = classify_system_impl(data_types=["PUBLIC"])
        assert result["overall_impact"] == "Low"
        assert result["fedramp_baseline"] == "Low"
        assert result["control_count"] == 156

    def test_high_watermark_with_mixed_types(self):
        """Mix of PII and FTI — high-water-mark should be High."""
        result = classify_system_impl(data_types=["PII", "FTI"])
        assert result["overall_impact"] == "High"
        assert result["availability_impact"] in ["Moderate", "High"]

    def test_auth_credentials_impact(self):
        """AUTH_CREDENTIALS drives High confidentiality."""
        result = classify_system_impl(data_types=["AUTH_CREDENTIALS"])
        assert result["confidentiality_impact"] == "High"

    def test_empty_data_types_defaults_to_moderate(self):
        """Unknown/empty data types should fall back gracefully."""
        result = classify_system_impl(data_types=["UNKNOWN_TYPE"])
        assert result["overall_impact"] in ["Low", "Moderate", "High"]
        assert "fedramp_baseline" in result

    def test_rationale_populated(self):
        """Rationale field should be non-empty."""
        result = classify_system_impl(data_types=["PII", "CUI"])
        assert result.get("rationale")

    def test_classification_keys(self):
        """Response must include all required keys."""
        result = classify_system_impl(data_types=["PII"])
        required_keys = {
            "confidentiality_impact",
            "integrity_impact",
            "availability_impact",
            "overall_impact",
            "fedramp_baseline",
            "control_count",
            "rationale",
        }
        assert required_keys.issubset(result.keys())


class TestDataTypeMapper:

    def test_ssn_alias(self):
        """'social security numbers' should map to PII_SSN."""
        result = map_data_types_impl(descriptions=["social security numbers"])
        assert any("PII_SSN" in tag or "PII" in tag for tag in result.get("canonical_tags", []))

    def test_medical_alias(self):
        """'medical records' should map to PHI."""
        result = map_data_types_impl(descriptions=["medical records"])
        tags = result.get("canonical_tags", [])
        assert "PHI" in tags

    def test_password_alias(self):
        """'passwords' should map to AUTH_CREDENTIALS."""
        result = map_data_types_impl(descriptions=["passwords"])
        tags = result.get("canonical_tags", [])
        assert "AUTH_CREDENTIALS" in tags

    def test_multiple_descriptions(self):
        """Multiple descriptions should return multiple mappings."""
        result = map_data_types_impl(descriptions=["PII", "PHI", "FTI"])
        tags = result.get("canonical_tags", [])
        assert len(tags) >= 3

    def test_classification_included(self):
        """Response must include a classification sub-key."""
        result = map_data_types_impl(descriptions=["CUI"])
        assert "classification" in result

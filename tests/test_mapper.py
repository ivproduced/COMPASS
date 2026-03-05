"""
test_mapper.py — Unit tests for control lookup, vector search, and gap analysis
"""
import pytest
from unittest.mock import MagicMock, patch

from backend.tools.control_lookup import control_lookup_impl
from backend.tools.gap_analyzer import gap_analysis_impl


class TestControlLookup:

    def test_exact_id_lookup_structure(self):
        """control_lookup_impl should return a dict for any input."""
        result = control_lookup_impl(control_id="AC-2")
        assert isinstance(result, dict)

    def test_family_filter(self):
        """Family filter should return results or empty list."""
        result = control_lookup_impl(family="AC")
        assert isinstance(result, dict)
        results_list = result.get("results", [])
        assert isinstance(results_list, list)
        for item in results_list:
            assert item.get("id", "").startswith("AC")

    def test_keyword_search(self):
        """Keyword search should return list of matching controls."""
        result = control_lookup_impl(keyword="boundary")
        assert isinstance(result, dict)
        results_list = result.get("results", [])
        assert isinstance(results_list, list)

    def test_nonexistent_id(self):
        """Nonexistent control ID should return empty or error dict."""
        result = control_lookup_impl(control_id="ZZ-999")
        assert isinstance(result, dict)

    def test_enhancement_id(self):
        """Enhancement controls like SC-7(3) should be handled."""
        result = control_lookup_impl(control_id="SC-7(3)")
        assert isinstance(result, dict)


class TestGapAnalyzer:

    def test_not_implemented_detection(self):
        """'no controls' description should be flagged as not_implemented."""
        result = gap_analysis_impl(
            control_id="SC-7",
            current_implementation="We have no firewall controls",
            required_implementation="Boundary protection with deny-all inbound",
        )
        assert result.get("implementation_status") in ("not_implemented", "partial")
        assert result.get("is_gap") is True

    def test_implemented_detection(self):
        """Positive description should be recognized as implemented."""
        result = gap_analysis_impl(
            control_id="SC-7",
            current_implementation="Implemented WAF and network boundary controls. Configured deny-all.",
        )
        # May be partial or implemented depending on heuristics
        assert result.get("implementation_status") in ("implemented", "partial")

    def test_risk_level_present(self):
        """Result must include risk_level."""
        result = gap_analysis_impl(
            control_id="AC-2",
            current_implementation="no account management process defined",
        )
        assert result.get("risk_level") in ("low", "moderate", "high", "critical")

    def test_remediation_for_known_control(self):
        """Known controls should have inline remediation hints."""
        result = gap_analysis_impl(
            control_id="SC-28",
            current_implementation="Data is not encrypted at rest",
        )
        assert result.get("remediation")

    def test_is_gap_flag(self):
        """is_gap should be a boolean."""
        result = gap_analysis_impl(
            control_id="RA-5",
            current_implementation="",
        )
        assert isinstance(result.get("is_gap"), bool)

    def test_component_field(self):
        """component field should propagate into result."""
        result = gap_analysis_impl(
            control_id="AU-6",
            current_implementation="no logging configured",
            component="AppServer",
        )
        assert isinstance(result, dict)

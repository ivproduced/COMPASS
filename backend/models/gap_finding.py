"""
Gap Finding — represents a compliance gap identified during assessment.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "moderate", "high", "critical"]
GapStatus = Literal["open", "in_progress", "closed"]
EffortEstimate = Literal["days", "weeks", "months"]


class GapFinding(BaseModel):
    finding_id: str = ""
    control_id: str                          # "SC-7"
    gap_title: str = ""                      # "Boundary Protection — No WAF"
    gap_description: str = ""
    risk_level: RiskLevel = "moderate"
    risk_description: str = ""
    remediation: str = ""
    estimated_effort: EffortEstimate = "weeks"
    target_date: str | None = None           # ISO date string
    status: GapStatus = "open"
    component_refs: list[str] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

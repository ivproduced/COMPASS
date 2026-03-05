"""
Control Assessment — maps NIST 800-53 controls to implementations.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ImplementationStatus = Literal[
    "implemented", "partial", "planned", "not_implemented", "not_assessed"
]


class ControlMapping(BaseModel):
    control_id: str                   # "AC-4"
    control_title: str = ""           # "Information Flow Enforcement"
    control_family: str = ""          # "Access Control"
    enhancement: str | None = None    # "(4)" for AC-4(4)
    implementation_status: ImplementationStatus = "not_assessed"
    implementation_description: str = ""
    component_refs: list[str] = Field(default_factory=list)
    evidence: str | None = None
    confidence_score: float = 0.0     # 0.0 – 1.0

    model_config = {"extra": "ignore"}


class ControlFamily(BaseModel):
    family_id: str       # "AC"
    family_name: str     # "Access Control"
    controls: list[ControlMapping] = Field(default_factory=list)

    @property
    def implemented_count(self) -> int:
        return sum(
            1 for c in self.controls
            if c.implementation_status in ("implemented", "partial")
        )

    @property
    def total_count(self) -> int:
        return len(self.controls)


class ComplianceScore(BaseModel):
    implemented: float = 0.0        # fraction 0–1
    partial: float = 0.0
    planned: float = 0.0
    not_addressed: float = 0.0
    total_controls: int = 0
    mapped_controls: int = 0

    @classmethod
    def from_mappings(cls, mappings: list[ControlMapping], baseline_total: int) -> "ComplianceScore":
        impl = sum(1 for m in mappings if m.implementation_status == "implemented")
        part = sum(1 for m in mappings if m.implementation_status == "partial")
        plan = sum(1 for m in mappings if m.implementation_status == "planned")
        mapped = len(mappings)
        not_addr = baseline_total - mapped
        total = baseline_total or 1  # avoid div/0
        return cls(
            implemented=impl / total,
            partial=part / total,
            planned=plan / total,
            not_addressed=not_addr / total,
            total_controls=baseline_total,
            mapped_controls=mapped,
        )

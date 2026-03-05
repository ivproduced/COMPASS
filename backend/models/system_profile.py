"""
System Profile — describes the system under assessment.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SystemComponent(BaseModel):
    name: str
    type: Literal[
        "frontend",
        "backend",
        "database",
        "storage",
        "network",
        "identity",
        "monitoring",
        "other",
    ]
    description: str
    provider: str | None = None   # e.g. "AWS", "GCP"
    service: str | None = None    # e.g. "Lambda", "Cloud Run"
    data_classification: str | None = None

    model_config = {"extra": "ignore"}


class Classification(BaseModel):
    confidentiality: Literal["low", "moderate", "high"] = "low"
    integrity: Literal["low", "moderate", "high"] = "low"
    availability: Literal["low", "moderate", "high"] = "low"
    overall: Literal["low", "moderate", "high"] = "low"
    fedramp_baseline: Literal["FedRAMP Low", "FedRAMP Moderate", "FedRAMP High"] = (
        "FedRAMP Low"
    )
    control_count: int = 156
    data_types_analyzed: list[str] = Field(default_factory=list)
    rationale: str = ""


class SystemProfile(BaseModel):
    system_name: str = ""
    description: str = ""
    data_types: list[str] = Field(default_factory=list)
    components: list[SystemComponent] = Field(default_factory=list)
    boundary_description: str = ""
    hosting_environment: Literal["cloud", "on_prem", "hybrid"] = "cloud"
    cloud_provider: str | None = None
    diagram_urls: list[str] = Field(default_factory=list)
    classification: Classification | None = None

    model_config = {"extra": "ignore"}

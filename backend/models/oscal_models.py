"""
OSCAL Models — metadata and document wrapper for OSCAL JSON output.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OSCALMetadata(BaseModel):
    title: str
    last_modified: str          # ISO-8601 UTC
    version: str = "1.0.0"
    oscal_version: str = "1.1.2"


class OSCALDocument(BaseModel):
    uuid: str
    metadata: OSCALMetadata
    document_type: Literal["ssp", "poam", "assessment_results"]
    content: dict[str, Any] = Field(default_factory=dict)
    validation_status: Literal["valid", "invalid", "pending"] = "pending"
    validation_errors: list[str] = Field(default_factory=list)
    gcs_path: str | None = None

    model_config = {"extra": "ignore"}

"""
Control Lookup Tool
Retrieves NIST SP 800-53 Rev 5 controls from the local JSON catalog.
Falls back gracefully when Vector Search is unavailable.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge" / "nist_800_53_rev5"


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, dict]:
    """Load the NIST 800-53 control catalog from local JSON files once."""
    catalog: dict[str, dict] = {}
    if not _KNOWLEDGE_DIR.exists():
        logger.warning("NIST 800-53 catalog directory not found: %s", _KNOWLEDGE_DIR)
        return catalog
    for fp in _KNOWLEDGE_DIR.glob("*.json"):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            # Support both single-control files and array files
            if isinstance(data, list):
                for ctrl in data:
                    if ctrl_id := ctrl.get("id"):
                        catalog[ctrl_id.upper()] = ctrl
                    # Index control enhancements (e.g. AC-2.1 nested under AC-2)
                    for enh in ctrl.get("enhancements", []):
                        if enh_id := enh.get("id"):
                            # Inherit family info from parent if not present
                            if "family" not in enh and "family" in ctrl:
                                enh = {**enh, "family": ctrl["family"], "family_title": ctrl.get("family_title", "")}
                            catalog[enh_id.upper()] = enh
            elif isinstance(data, dict):
                if ctrl_id := data.get("id"):
                    catalog[ctrl_id.upper()] = data
                for enh in data.get("enhancements", []):
                    if enh_id := enh.get("id"):
                        if "family" not in enh and "family" in data:
                            enh = {**enh, "family": data["family"], "family_title": data.get("family_title", "")}
                        catalog[enh_id.upper()] = enh
        except Exception as exc:
            logger.error("Failed to load control file %s: %s", fp, exc)
    logger.info("Loaded %d controls from local catalog", len(catalog))
    return catalog


def control_lookup_impl(
    control_id: str | None = None,
    family: str | None = None,
    keyword: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Look up NIST 800-53 Rev 5 controls by ID, family, or keyword.

    Args:
        control_id: Specific control ID (e.g. "AC-4", "SC-7(3)").
        family:     Two-letter family code (e.g. "AC", "SC", "AU").
        keyword:    Free-text search against title and description.
        limit:      Maximum number of results to return (default 10).

    Returns:
        Dict with controls list and match count.
    """
    catalog = _load_catalog()
    results: list[dict] = []

    if control_id:
        key = control_id.strip().upper()
        if ctrl := catalog.get(key):
            return {"controls": [ctrl], "count": 1, "source": "catalog"}
        # Partial match (e.g. "SC-7" should also return SC-7(1), SC-7(2)…)
        prefix_matches = [v for k, v in catalog.items() if k.startswith(key)]
        return {"controls": prefix_matches[:limit], "count": len(prefix_matches), "source": "catalog"}

    if family:
        fam = family.strip().upper()
        results = [v for k, v in catalog.items() if k.startswith(fam + "-")]

    if keyword:
        # Split query into individual words and match controls containing ANY word.
        # Stopwords are skipped; controls matching more words rank higher.
        _STOP = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "is", "it", "on", "at", "by", "with"}
        words = [w for w in keyword.lower().split() if w not in _STOP and len(w) > 1]
        if not words:
            words = [keyword.lower()]
        scored: list[tuple[int, dict]] = []
        for ctrl in catalog.values():
            haystack = " ".join([
                ctrl.get("title", ""),
                ctrl.get("description", ""),
                ctrl.get("supplemental_guidance", ""),
            ]).lower()
            hits = sum(1 for w in words if w in haystack)
            if hits:
                scored.append((hits, ctrl))
        scored.sort(key=lambda t: t[0], reverse=True)
        kw_results = [ctrl for _, ctrl in scored]
        if results:
            # Intersect with family filter
            ids_in_family = {r.get("id") for r in results}
            results = [r for r in kw_results if r.get("id") in ids_in_family]
        else:
            results = kw_results

    return {
        "controls": results[:limit],
        "count": len(results),
        "source": "catalog",
        "truncated": len(results) > limit,
    }


control_lookup_tool = FunctionTool(func=control_lookup_impl)

"""Convert OSCAL 800-53 catalog and extract 800-60 information types."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OSCAL_CONTENT = REPO_ROOT.parent / "oscal-content"

# --- 800-53 conversion ---
CATALOG_IN = OSCAL_CONTENT / "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"
CATALOG_OUT = REPO_ROOT / "backend/knowledge/nist_800_53_rev5/nist_800_53_rev5_catalog.json"


def extract_prose(parts, depth=0):
    texts = []
    for part in (parts or []):
        prose = part.get("prose", "")
        if prose:
            texts.append(prose.strip())
        sub = part.get("parts", [])
        if sub:
            texts.extend(extract_prose(sub, depth + 1))
    return texts


def convert_control(ctrl, family_id, family_title):
    ctrl_id = ctrl["id"].upper()
    prose_parts = []
    for part in ctrl.get("parts", []):
        if part.get("name") in ("statement", "guidance"):
            prose_parts.extend(extract_prose([part]))
    description = " ".join(prose_parts)[:2000]

    params = [
        {"id": p.get("id", ""), "label": p.get("label", "")}
        for p in ctrl.get("params", [])
        if p.get("label")
    ]

    enhancements = []
    for enh in ctrl.get("controls", []):
        enh_id = enh["id"].upper()
        enh_prose = []
        for part in enh.get("parts", []):
            if part.get("name") == "statement":
                enh_prose.extend(extract_prose([part]))
        enhancements.append({
            "id": enh_id,
            "title": enh.get("title", ""),
            "description": " ".join(enh_prose)[:500],
        })

    return {
        "id": ctrl_id,
        "title": ctrl.get("title", ""),
        "family": family_id.upper(),
        "family_title": family_title,
        "description": description,
        "parameters": params,
        "enhancements": enhancements,
    }


def convert_800_53():
    print(f"Reading: {CATALOG_IN}")
    with open(CATALOG_IN) as f:
        data = json.load(f)

    catalog = data.get("catalog", data)
    controls_out = []

    for group in catalog.get("groups", []):
        family_id = group.get("id", "").upper()
        family_title = group.get("title", "")
        for ctrl in group.get("controls", []):
            controls_out.append(convert_control(ctrl, family_id, family_title))

    CATALOG_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_OUT, "w") as f:
        json.dump(controls_out, f, indent=2)

    print(f"Written {len(controls_out)} controls to {CATALOG_OUT}")
    return controls_out


# --- 800-60 extraction ---
BRANCH_800_60 = "add-sp800-60-information-types"
FILE_800_60 = "nist.gov/SP800-60/v2r1/json/NIST_SP800-60_information_types.json"
OUT_800_60 = REPO_ROOT / "backend/knowledge/nist_800_60/information_types.json"

FIPS_MAP = {
    "fips-199-low": "low",
    "fips-199-moderate": "moderate",
    "fips-199-high": "high",
}


def convert_800_60():
    print(f"Extracting 800-60 from branch: {BRANCH_800_60}")
    result = subprocess.run(
        ["git", "show", f"{BRANCH_800_60}:{FILE_800_60}"],
        cwd=str(OSCAL_CONTENT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return []

    data = json.loads(result.stdout)
    info_types = data.get("information-types", [])

    out = []
    for it in info_types:
        c_level = FIPS_MAP.get(it.get("confidentiality-impact", {}).get("selected", ""), "low")
        i_level = FIPS_MAP.get(it.get("integrity-impact", {}).get("selected", ""), "low")
        a_level = FIPS_MAP.get(it.get("availability-impact", {}).get("selected", ""), "low")
        ids = []
        for cat in it.get("categorizations", []):
            ids.extend(cat.get("information-type-ids", []))
        out.append({
            "id": ids[0] if ids else "",
            "title": it.get("title", ""),
            "description": it.get("description", "")[:300],
            "confidentiality": c_level,
            "integrity": i_level,
            "availability": a_level,
        })

    OUT_800_60.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_800_60, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Written {len(out)} information types to {OUT_800_60}")
    return out


# --- FedRAMP baseline extraction ---
FEDRAMP_AUTOMATION = REPO_ROOT.parent / "fedramp-automation"
FEDRAMP_SRC = FEDRAMP_AUTOMATION / "dist/content/rev5/baselines/json"
FEDRAMP_DEST = REPO_ROOT / "backend/knowledge/fedramp"

BASELINES = ["LOW", "MODERATE", "HIGH", "LI-SaaS"]


def extract_fedramp_baselines():
    if not FEDRAMP_SRC.exists():
        print(f"ERROR: fedramp-automation repo not found at {FEDRAMP_AUTOMATION}")
        return {}

    FEDRAMP_DEST.mkdir(parents=True, exist_ok=True)
    results = {}

    for bl in BASELINES:
        src_file = FEDRAMP_SRC / f"FedRAMP_rev5_{bl}-baseline_profile.json"
        if not src_file.exists():
            print(f"NOT FOUND: {src_file}")
            continue

        with open(src_file, encoding="utf-8") as f:
            d = json.load(f)

        profile = d.get("profile", d)
        ids = []
        for imp in profile.get("imports", []):
            for inc in imp.get("include-controls", []):
                ids.extend(inc.get("with-ids", []))

        ids = sorted(set(c.upper() for c in ids))
        key = bl.lower().replace("-", "_")
        out_name = f"fedramp_rev5_{key}_baseline.json"
        out_path = FEDRAMP_DEST / out_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ids, f, indent=2)

        results[bl] = len(ids)
        print(f"FedRAMP {bl}: {len(ids)} controls -> {out_name}")

    # Also write a combined index for easy lookup
    index = {}
    for bl in BASELINES:
        key = bl.lower().replace("-", "_")
        fp = FEDRAMP_DEST / f"fedramp_rev5_{key}_baseline.json"
        if fp.exists():
            with open(fp) as f:
                index[bl] = json.load(f)
    with open(FEDRAMP_DEST / "baselines_index.json", "w") as f:
        json.dump(index, f, indent=2)
    print(f"Wrote baselines_index.json with {len(index)} baselines")

    return results


if __name__ == "__main__":
    controls = convert_800_53()
    info_types = convert_800_60()
    fedramp = extract_fedramp_baselines()
    print(f"\nDone. 800-53: {len(controls)} controls, 800-60: {len(info_types)} info types, FedRAMP: {fedramp}")

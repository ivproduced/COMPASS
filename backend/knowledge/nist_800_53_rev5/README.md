# NIST SP 800-53 Rev 5 Control Catalog

Place the NIST SP 800-53 Rev 5 JSON control catalog file(s) in this directory.

## Expected File Format

Each JSON file should contain an array of control objects:

```json
[
  {
    "id": "AC-1",
    "title": "Policy and Procedures",
    "family": "AC",
    "description": "...",
    "parameters": [...],
    "enhancements": [...]
  }
]
```

## Source

Download the official catalog from NIST:
https://csrc.nist.gov/projects/risk-management/sp800-53-controls/release-search

Or use the OSCAL-formatted catalog:
https://github.com/usnistgov/OSCAL/tree/main/content/NIST_SP-800-53_rev5

## Files Expected by control_lookup.py

- `nist_800_53_rev5_catalog.json` — full control catalog
- (Optional) `fedramp_low_baseline.json` — FedRAMP Low baseline control IDs
- (Optional) `fedramp_moderate_baseline.json` — FedRAMP Moderate baseline control IDs
- (Optional) `fedramp_high_baseline.json` — FedRAMP High baseline control IDs

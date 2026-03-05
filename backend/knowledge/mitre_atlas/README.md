# MITRE ATLAS Knowledge Corpus

Place MITRE ATLAS AI/ML attack technique files in this directory.

## Expected Format

JSON files containing technique-to-control mappings:

```json
[
  {
    "technique_id": "AML.T0043",
    "name": "Craft Adversarial Data",
    "tactic": "Machine Learning Attack Staging",
    "description": "...",
    "mitigating_controls": ["SI-3", "SC-28", "SA-11"],
    "ai_overlay_controls": ["SC-7(10)", "SA-9"]
  }
]
```

## Source

- MITRE ATLAS: https://atlas.mitre.org/techniques
- NIST AI RMF: https://airc.nist.gov/
- CISA AI Guidance: https://www.cisa.gov/ai

## Notes

`threat_lookup.py` includes inline mappings for the 7 most common ATLAS techniques.
Additional techniques loaded from `*.json` files in this directory will supplement the inline mappings.

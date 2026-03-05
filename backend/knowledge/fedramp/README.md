# FedRAMP Guidance Documents

Place FedRAMP-specific guidance and templates in this directory.

## Expected Files

- `fedramp_security_controls.json` — FedRAMP-specific control parameters and guidance
- `fedramp_ssp_template.json` — SSP template structure reference
- `ato_checklist.json` — Authorization to Operate checklist items

## Source

- FedRAMP Program Office: https://www.fedramp.gov/documents-templates/
- FedRAMP Marketplace: https://marketplace.fedramp.gov/
- FedRAMP GitHub: https://github.com/GSA/fedramp-automation

## Notes

COMPASS uses FedRAMP Low/Moderate/High baseline control counts embedded in
`backend/tools/classify_system.py`. Additional guidance documents here will
be used by the mapper and gap agents to provide FedRAMP-specific remediation advice.

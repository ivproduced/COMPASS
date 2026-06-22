"""Provider-agnostic tool schema definitions for COMPASS.

Each entry is an OpenAI-compatible tool dict:
  { "name": str, "description": str, "parameters": <JSON-Schema object> }

Both the Gemini and OpenAI providers import this list and convert to their
native formats. The Live WebSocket (Gemini native-audio) does NOT use these —
it intentionally omits tool declarations because native-audio Live models only
support bidiGenerateContent. Tools run via the sidecar generate_content call.
"""

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "classify_system",
        "description": "Classify a system using FIPS 199 based on data types processed.",
        "parameters": {
            "type": "object",
            "properties": {
                "data_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of canonical data type tags. Use the most specific tag available. "
                        "PHI subtypes: PHI_CLINICAL (EHR/patient records), PHI_MENTAL_HEALTH, "
                        "PHI_SUBSTANCE_ABUSE, PHI_GENETIC, PHI_BILLING (insurance/billing), PHI_ADMIN. "
                        "PII subtypes: PII, PII_SSN, PII_FINANCIAL, PII_BIOMETRIC, PII_LOCATION. "
                        "Other: FTI, CJIS, CUI, CUI_CONTROLLED, CUI_EXPORT, FINANCIAL, PAYMENT_CARD, "
                        "AUTH_CREDENTIALS, CRYPTOGRAPHIC_KEYS, TRADE_SECRET, PUBLIC, INTERNAL."
                    ),
                },
                "system_description": {
                    "type": "string",
                    "description": "Optional system description",
                },
                "confidentiality_override": {
                    "type": "string",
                    "description": (
                        "Explicit confidentiality impact level stated by the user: 'low', 'moderate', or 'high'. "
                        "Only set if the user has clearly stated a specific confidentiality level."
                    ),
                },
                "integrity_override": {
                    "type": "string",
                    "description": (
                        "Explicit integrity impact level stated by the user: 'low', 'moderate', or 'high'. "
                        "Only set if the user has clearly stated a specific integrity level."
                    ),
                },
                "availability_override": {
                    "type": "string",
                    "description": (
                        "Explicit availability impact level stated by the user: 'low', 'moderate', or 'high'. "
                        "Only set if the user has clearly stated a specific availability level. "
                        "Example: if user says 'availability can be moderate', pass 'moderate'."
                    ),
                },
            },
            "required": ["data_types"],
        },
    },
    {
        "name": "map_data_types",
        "description": (
            "Map free-text data type descriptions to canonical tags and C/I/A impact levels. "
            "Pass the most specific phrase possible so the right tag is chosen. "
            "PHI subtypes: 'medical records'→PHI_CLINICAL, 'mental health records'→PHI_MENTAL_HEALTH, "
            "'substance abuse records'→PHI_SUBSTANCE_ABUSE, 'genetic data'→PHI_GENETIC, "
            "'medical billing'→PHI_BILLING, 'health care administration'→PHI_ADMIN. "
            "Other examples: 'electronic health records'→PHI_CLINICAL, 'EHR'→PHI_CLINICAL, "
            "'ssn'→PII_SSN, 'credit card data'→PAYMENT_CARD, 'encryption keys'→CRYPTOGRAPHIC_KEYS, "
            "'criminal justice information'→CJIS, 'federal tax information'→FTI."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "descriptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific data type phrases, one per item",
                }
            },
            "required": ["descriptions"],
        },
    },
    {
        "name": "search_controls",
        "description": "Semantic search over NIST 800-53 controls for a component or requirement.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Component or requirement to map to controls",
                },
                "family_filter": {
                    "type": "string",
                    "description": "Optional: restrict to a control family (AC, SC, AU…)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "control_lookup",
        "description": "Look up a specific NIST 800-53 control by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Control ID (e.g. AC-4, SC-7(3))",
                },
                "keyword": {
                    "type": "string",
                    "description": "Keyword to search by title or description",
                },
            },
        },
    },
    {
        "name": "gap_analysis",
        "description": "Analyze a compliance gap for a specific control.",
        "parameters": {
            "type": "object",
            "properties": {
                "control_id": {"type": "string"},
                "current_implementation": {
                    "type": "string",
                    "description": (
                        "CRITICAL: Quote the user's EXACT words about this control's implementation. "
                        "Do NOT paraphrase, summarize, or rewrite. If the user said it is NOT implemented, "
                        "missing, absent, or not in place, those exact words MUST appear here. "
                        "Examples: 'MFA is NOT implemented', 'we have no logging', "
                        "'encryption is not configured', 'we don't have this in place'. "
                        "The gap scoring engine reads this field literally — paraphrasing breaks detection."
                    ),
                },
                "required_implementation": {"type": "string"},
                "component": {"type": "string"},
            },
            "required": ["control_id", "current_implementation"],
        },
    },
    {
        "name": "generate_oscal",
        "description": "Generate OSCAL-formatted SSP or POA&M from session assessment data.",
        "parameters": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": ["ssp", "poam", "assessment_results"],
                },
                "system_name": {"type": "string"},
                "system_description": {"type": "string"},
                "fips_199_level": {"type": "string"},
            },
            "required": ["document_type"],
        },
    },
    {
        "name": "threat_lookup",
        "description": "Query MITRE ATLAS AI/ML threat mappings to find mitigating controls.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "technique_id": {"type": "string"},
                "tactic": {"type": "string"},
            },
        },
    },
]

"""
COMPASS Classifier Agent
Responsible for extracting data types from system descriptions
and performing FIPS 199 impact classification.
"""
from __future__ import annotations

from google.adk.agents import Agent

from backend.tools.classify_system import classify_system_tool
from backend.tools.data_type_mapper import map_data_types_tool

CLASSIFIER_INSTRUCTION = """
You are the COMPASS Classifier Agent. Your sole responsibility is FIPS 199 system classification.

When activated, you:
1. Review the system description and conversation history provided.
2. Extract all data types mentioned (PII, PHI, CUI, FTI, financial data, credentials, etc.).
3. Map extracted descriptions to canonical data type tags using map_data_types.
4. Run classify_system with the canonical tags.
5. Return a structured classification result with:
   - Confidentiality, Integrity, Availability impact levels
   - Overall impact level and FedRAMP baseline (Low/Moderate/High)
   - The data types that drove the classification
   - A brief rationale explaining which data type drove the high-water-mark

Be precise. If you're uncertain about a data type's classification, note it as "moderate" 
and flag it for confirmation. Always ask if the architect handles FTI (Federal Tax Information) 
or PHI (Protected Health Information) — these drive the impact to High.
""".strip()

classifier_agent = Agent(
    model="gemini-2.5-pro",
    name="compass_classifier",
    description=(
        "Classifies systems using FIPS 199 based on data types processed. "
        "Determines FedRAMP baseline (Low/Moderate/High) and control count."
    ),
    instruction=CLASSIFIER_INSTRUCTION,
    tools=[classify_system_tool, map_data_types_tool],
)

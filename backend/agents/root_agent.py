"""
COMPASS Root Agent
Orchestrates the full assessment conversation through specialist sub-agents.
This is the agent wired into the Gemini Live API session.
"""
from __future__ import annotations

from google.adk.agents import Agent

from backend.agents.classifier_agent import classifier_agent
from backend.agents.mapper_agent import mapper_agent
from backend.agents.gap_agent import gap_agent
from backend.agents.oscal_agent import oscal_agent
from backend.agents.prompts import COMPASS_SYSTEM_PROMPT
from backend.tools.classify_system import classify_system_tool
from backend.tools.control_lookup import control_lookup_tool
from backend.tools.data_type_mapper import map_data_types_tool
from backend.tools.gap_analyzer import gap_analysis_tool
from backend.tools.oscal_generator import generate_oscal_tool
from backend.tools.oscal_validator import validate_oscal_tool
from backend.tools.threat_lookup import threat_lookup_tool
from backend.tools.vector_search import search_controls_tool

root_agent = Agent(
    model="gemini-2.5-pro",
    name="compass_root",
    description=(
        "COMPASS — FedRAMP Compliance Mapping & Policy Assessment Speech System. "
        "Orchestrates real-time voice-driven FedRAMP assessments through specialist sub-agents."
    ),
    instruction=COMPASS_SYSTEM_PROMPT,
    tools=[
        classify_system_tool,
        control_lookup_tool,
        map_data_types_tool,
        search_controls_tool,
        gap_analysis_tool,
        generate_oscal_tool,
        validate_oscal_tool,
        threat_lookup_tool,
    ],
    sub_agents=[
        classifier_agent,
        mapper_agent,
        gap_agent,
        oscal_agent,
    ],
)

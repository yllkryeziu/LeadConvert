# import os
# import uuid
# import json
# import asyncio
# import logging
# from google.adk.agents import LlmAgent, SequentialAgent
# from google.adk.tools import FunctionTool
# from google.adk.runners import Runner
# from google.adk.sessions import InMemorySessionService
# from google.genai import types
# from research_personal_agent.tools import (
#     extract_contacts as _extract_contacts,
#     perform_research as _perform_research,
#     build_persona as _build_persona,
#     draft_email as _draft_email,
# )
# from dotenv import load_dotenv

# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# GEMINI_MODEL = "gemini-2.0-flash"
# APP_NAME = "research_persona_agent_app"


# # ---------------------------
# # Tool wrappers (align to ADK tool calling)
# # ---------------------------
# def tool_extract_contacts(company_name: str) -> str:
#     """Adapter around extract_contacts(company_name) → JSON string."""
#     return _extract_contacts(company_name)


# def tool_perform_research(company_name: str) -> str:
#     """Adapter around perform_research(company_name) → JSON string."""
#     return _perform_research(company_name)


# def tool_build_persona(company_name: str, contacts: str, research: str) -> str:
#     """Adapter to bridge signature; original build_persona expects a JSON blob."""
#     payload = json.dumps(
#         {
#             "company_name": company_name,
#             "contacts": contacts,
#             "research": research,
#         }
#     )
#     return _build_persona(payload)


# def tool_draft_email(contacts: str, persona: str) -> str:
#     """Adapter to bridge signature; original draft_email expects a JSON blob."""
#     payload = json.dumps(
#         {
#             "contacts": contacts,
#             "persona": json.loads(persona) if isinstance(persona, str) else persona,
#         }
#     )
#     return _draft_email(payload)

# # Sub-agent: Contact Extraction
# contact_agent = LlmAgent(
#     name="ContactAgent",
#     model=GEMINI_MODEL,
#     description="Extract contact emails and phone numbers.",
#     instruction=(
#         "Call tool_extract_contacts(company_name=\"{company_name}\") and return the output."
#     ),
#     tools=[FunctionTool(tool_extract_contacts)],
#     output_key="contacts",
# )

# # Sub-agent: Research Collection
# research_agent = LlmAgent(
#     name="ResearchAgent",
#     model=GEMINI_MODEL,
#     description="Gather mission, values, and news summaries.",
#     instruction=(
#         "Call tool_perform_research(company_name=\"{company_name}\") and return the output."
#     ),
#     tools=[FunctionTool(tool_perform_research)],
#     output_key="research",
# )

# # Sub-agent: Persona Building
# persona_agent = LlmAgent(
#     name="PersonaAgent",
#     model=GEMINI_MODEL,
#     description="Builds a detailed persona from contacts and research.",
#     instruction=(
#         "Call tool_build_persona(company_name=\"{company_name}\", contacts=\"{contacts}\", "
#         "research=\"{research}\") and return the output."
#     ),
#     tools=[FunctionTool(tool_build_persona)],
#     output_key="persona",
# )

# # Sub-agent: Email Drafting
# pitch_agent = LlmAgent(
#     name="PitchAgent",
#     model=GEMINI_MODEL,
#     description="Drafts a personalized email pitch.",
#     instruction=(
#         "Call tool_draft_email(contacts=\"{contacts}\", persona=\"{persona}\") and return the output."
#     ),
#     tools=[FunctionTool(tool_draft_email)],
#     output_key="pitch",
# )

# # Root SequentialAgent
# root_agent = SequentialAgent(
#     name="ResearchPersonaPipeline",
#     sub_agents=[contact_agent, research_agent, persona_agent, pitch_agent],
#     description="Extracts contacts, researches company, builds persona, drafts email.",
# )


# async def main(company: str):
#     session_service = InMemorySessionService()
#     user_id = "user_001"
#     session_id = str(uuid.uuid4())
#     await session_service.create_session(
#         app_name=APP_NAME,
#         user_id=user_id,
#         session_id=session_id
#     )

#     # Initialize all required state keys
#     initial_state = {
#         "company_name": company,
#         "contacts": "",
#         "research": "",
#         "persona": "",
#         "pitch": ""
#     }

#     runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

#     user_message = types.Content(parts=[types.Part(text=f"Research data for {company}")])

#     events = runner.run(
#         user_id=user_id,
#         session_id=session_id,
#         new_message=user_message,
#         initial_state=initial_state
#     )

#     for event in events:
#         if event.is_final_response():
#             print("Final Output:\n", event.content.parts[0].text)
#             break

# if __name__ == "__main__":
#     import sys
#     asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "Tech Innovators Inc"))


from dotenv import load_dotenv
from google.adk.agents import SequentialAgent

from .sub_agent import persona_creator, research_agent, email_creator

load_dotenv()

# `root_agent` defines a simple pipeline where each sub-agent runs in order.
# Use SequentialAgent when later steps depend on outputs produced by earlier steps.
# In this pipeline:
#  - `positive_critic` runs first to provide a positive critique,
#  - `negative_critic` runs next to provide a negative critique,
#  - `review_critic` runs last to review combined outputs and produce a final evaluation.
root_agent = SequentialAgent(
    name="pipeline_agent",
    sub_agents=[research_agent, persona_creator, email_creator],
    description="This is an agent that sequentially executes agents(positive_critic, negative_critic, review_critic)",
)
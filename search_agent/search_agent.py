import json
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import Session, InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from entities.context import ContextData
from entities.metadata import TopResults, Metadata

APP_NAME="google_search_agent"
USER_ID="someuser" # TODO: Replace with actual user ID
SESSION_ID="somesession" # TODO: Replace with actual session ID

root_agent = Agent(
    name=APP_NAME,
    model="gemini-2.5-flash",
    description="Agent to answer questions using Google Search",
    instruction="You are searching agent which answers given questions by searching the internet",
    # google_search is a pre-built tool which allows the agent to perform Google searches.
    tools=[google_search],
)

async def setup_session_service():
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    return session_service

# Agent Interaction
def call_agent(query: str) -> str:
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session_service = asyncio.run(setup_session_service())
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            return final_response

def extract_json(text: str) -> dict:
    """Extract JSON from a code block in the text."""
    try:
        return json.loads(text.split("```json")[1].split("```")[0])
    except (IndexError, json.JSONDecodeError):
        return None

def get_top_results(context_data: ContextData) -> TopResults:
    profile = context_data.get_profile()
    client = context_data.get_client()
    criterias = context_data.get_criterias()

    query = f"""
    You are an expert in finding information on the internet. Your goal is to find the best possible results for the user based on their profile, their goal and the provided criterias.
    Profile: {profile}
    Target Client: {client}
    Criterias: {criterias}
    Please provide a list of top 5 results that best match the user's goal and criterias.
    """
    constraint = """Only return the JSON object, do not include any other text.
    IMPORTANT: Return your response as a JSON object matching this structure:
    {
        "name": "The name of the retrieved result.",
        "location": "The location of the retrieved result."
    }
    """
    prompt = query + constraint
    retry_count = 5
    while retry_count > 0:
        response = call_agent(prompt)
        results = extract_json(response)
        if results:
            try:
                return TopResults(results=results)
            except:
                pass
        retry_count -= 1
    return TopResults(results=[])

def extract_metadata(matter: str) -> Metadata | None:
    query = f"What is '{matter}'?"
    constraint ="""Only return the JSON object, do not include any other text.
    IMPORTANT: Return your response as a JSON object matching this structure:
    {
        "name": "The name of the entity being described.",
        "address": "The address of the entity being described.",
        "phone_number": "The phone number of the entity being described.",
        "email": "The email address of the entity being described.",
        "website": "The website of the entity being described.",
        "review_rate": "The review rate of the entity being described.",
        "number_of_reviews": "The number of reviews for the entity being described.",
        "description": "A description of the entity being described."
    }
    """
    prompt = query + constraint
    retry_count = 5
    while retry_count > 0:
        response = call_agent(prompt)
        result = extract_json(response)
        if result:
            try:
                return Metadata(**result)
            except:
                pass
        retry_count -= 1
    return None

def process_context_data(data: dict):
    context_data = ContextData(**data)
    results = get_top_results(context_data).results
    final_results = []
    for result in results:
        if result is None:
            continue
        name = result.name
        location = result.location
        if name is None or location is None:
            continue
        matter = f"{name} in {location}"
        metadata = extract_metadata(matter)
        if metadata:
            final_results.append(metadata)
    return final_results


## Example usage
# from sub_agents import search_agent
# search_agent.process_context_data({
#     "user_info": {
#         "service_provided": "building and optimizing high-end Shopify e-commerce websites",
#         "unique_value_prop": "Creating a premium, luxury user experience that is proven to increase conversion rates for exclusive brands.",
#         "core_messaging": {
#             "specific_pain_points_solved": [
#                 "a slow, clunky website that frustrates users",
#                 "a confusing checkout process that leads to high cart abandonment",
#                 "a generic site design that fails to communicate their premium brand identity"
#             ],
#             "key_benefits_and_outcomes": [
#                 "a much faster and more beautiful website",
#                 "a measurable increase in online sales, typically around 15-20%",
#                 "a stronger, more professional brand image"
#             ],
#             "competitor_differentiators": [
#                 "a fully bespoke design tailored to each client, unlike agencies that use templates",
#                 "includes 3 months of post-launch performance monitoring and optimization"
#             ]
#         }
#     },
#     "ideal_client": {
#         "company_profile": {
#             "industry_niche": "Direct-to-consumer (DTC) industry, specifically focusing on niches like independent fashion labels and high-end consumer goods.",
#             "company_size": "5 to 30 employees",
#             "location": "North America (USA and Canada)"
#         },
#         "opportunity_signals": {
#             "green_flags": [
#                 "brand gets a feature in a major publication (e.g., Vogue)",
#                 "hiring for a new marketing position",
#                 "current website has a low score on Google PageSpeed Insights"
#             ],
#             "red_flags": [
#                 "brands that sell most of their products on Amazon",
#                 "companies that have had recent public layoffs",
#                 "business has been operating for less than a year"
#             ]
#         }
#     }
# })

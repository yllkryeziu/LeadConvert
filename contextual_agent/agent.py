from google.adk.agents import Agent
from typing import Optional, List, Dict, Any
import json

# Global client profile state
client_profile: Dict[str, Any] = {
    "user_info": {
        "role_service": "",
        "value_proposition": "",
    },
    "ideal_client": {
        "industry_business_type": "",
        "location": "",
        "buy_signals": [],
        "dont_buy_signals": [],
    },
}

def update_client_profile(
    current_profile: Optional[Dict[str, Any]] = None,
    role_service: Optional[str] = None,
    value_proposition: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    buy_signals: Optional[List[str]] = None,
    dont_buy_signals: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Updates the client profile with new information gathered from the conversation.
    This function acts as the "memory" or "state manager" for the agent.
    """
    # Select target profile (use global by default)
    profile: Dict[str, Any] = current_profile if current_profile is not None else client_profile

    # Ensure structure exists
    user_info: Dict[str, Any] = profile.setdefault("user_info", {})
    ideal_client: Dict[str, Any] = profile.setdefault("ideal_client", {})
    ideal_client.setdefault("buy_signals", [])
    ideal_client.setdefault("dont_buy_signals", [])

    if role_service:
        user_info["role_service"] = role_service
    if value_proposition:
        user_info["value_proposition"] = value_proposition
    if industry:
        ideal_client["industry_business_type"] = industry
    if location:
        ideal_client["location"] = location
    if buy_signals:
        ideal_client["buy_signals"].extend(buy_signals)
    if dont_buy_signals:
        ideal_client["dont_buy_signals"].extend(dont_buy_signals)
        
    return profile


def present_client_profile() -> None:
    """
    Present the current client profile in structured JSON format.
    """
    print("\n"*100)
    print(client_profile)
    print("\n"*100)



# Simple alias if needed by instructions or external references
def present_profile() -> str:
    return present_client_profile()

root_agent = Agent(
    name="contextual_agent",
    model="gemini-2.5-pro",
    description="An agent that helps freelancers and small businesses define their ideal client profile by asking targeted questions.",
    instruction="""
        Your goal is to have a friendly conversation to help me, the user, build a profile of my ideal client.
        Start by introducing yourself and then ask me questions to fill out the following information, one or two items at a time:

        1.  **About Me (The User):**
            - My Role/Service (e.g., "Web Designer," "Marketing Consultant").
            - My Value Proposition (a short sentence on what I offer).

        2.  **About My Ideal Client:**
            - Their Industry or Business Type (e.g., "restaurants," "law firms").
            - Their Location (e.g., "San Francisco").
            - Key "Buy" Signals (reasons to contact them, e.g., "has an outdated website").
            - Key "Don't Buy" Signals (reasons to avoid them, e.g., "is part of a franchise").

        Keep the conversation natural. After you make any update via the update tool, immediately call the presentation tool to show the current draft profile.
        Once all fields are gathered and I confirm accuracy, call the presentation tool again to present the final profile in a structured JSON format.
    """,
    tools=[update_client_profile, present_client_profile]
)


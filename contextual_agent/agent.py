from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from typing import Optional, List, Dict, Any
import json
from .sub_agents.profile_checker_agent import profile_checker_agent

client_profile: Dict[str, Any] = {
  "user_info": {
    "service_provided": "",
    "unique_value_prop": "",
    "core_messaging": {
        "specific_pain_points_solved": [],
        "key_benefits_and_outcomes": [],
        "competitor_differentiators": []
    }
  },
  "ideal_client": {
    "company_profile": {
      "industry_niche": "",
      "company_size": "",
      "location": ""
    },
    "opportunity_signals": {
      "green_flags": [],
      "red_flags": []
    }
  }
}


def update_client_profile(
    current_profile: Optional[Dict[str, Any]] = None,
    service_provided: Optional[str] = None,
    unique_value_prop: Optional[str] = None,
    specific_pain_points_solved: Optional[List[str]] = None,
    key_benefits_and_outcomes: Optional[List[str]] = None,
    competitor_differentiators: Optional[List[str]] = None,
    industry_niche: Optional[str] = None,
    company_size: Optional[str] = None,
    location: Optional[str] = None,
    green_flags: Optional[List[str]] = None,
    red_flags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Updates the client profile with new information gathered from the conversation.
    This function acts as the "memory" or "state manager" for the agent.

    Args:
        current_profile (Optional[Dict[str, Any]]): The profile to update. Defaults to the global profile.
        service_provided (Optional[str]): A description of the user's primary service offering.
        unique_value_prop (Optional[str]): The user's unique value proposition.
        specific_pain_points_solved (Optional[List[str]]): A list of client problems the user's service solves.
        key_benefits_and_outcomes (Optional[List[str]]): A list of tangible results clients can expect.
        competitor_differentiators (Optional[List[str]]): A list of factors that make the user's service unique.
        industry_niche (Optional[str]): The specific industry or niche of the ideal client company.
        company_size (Optional[str]): The size of the ideal client company (e.g., "10-50 employees").
        location (Optional[str]): The geographical location of the ideal client.
        green_flags (Optional[List[str]]): A list of positive signals indicating a good time to engage.
        red_flags (Optional[List[str]]): A list of negative signals indicating a reason to avoid contact.
    """
    profile: Dict[str, Any] = current_profile if current_profile is not None else client_profile

    # Ensure nested structures exist
    user_info = profile.setdefault("user_info", {})
    core_messaging = user_info.setdefault("core_messaging", {})
    core_messaging.setdefault("specific_pain_points_solved", [])
    core_messaging.setdefault("key_benefits_and_outcomes", [])
    core_messaging.setdefault("competitor_differentiators", [])

    ideal_client = profile.setdefault("ideal_client", {})
    company_profile = ideal_client.setdefault("company_profile", {})
    opportunity_signals = ideal_client.setdefault("opportunity_signals", {})
    opportunity_signals.setdefault("green_flags", [])
    opportunity_signals.setdefault("red_flags", [])

    # Update user_info
    if service_provided:
        user_info["service_provided"] = service_provided
    if unique_value_prop:
        user_info["unique_value_prop"] = unique_value_prop
    if specific_pain_points_solved:
        core_messaging["specific_pain_points_solved"].extend(specific_pain_points_solved)
    if key_benefits_and_outcomes:
        core_messaging["key_benefits_and_outcomes"].extend(key_benefits_and_outcomes)
    if competitor_differentiators:
        core_messaging["competitor_differentiators"].extend(competitor_differentiators)

    # Update ideal_client.company_profile
    if industry_niche:
        company_profile["industry_niche"] = industry_niche
    if company_size:
        company_profile["company_size"] = company_size
    if location:
        company_profile["location"] = location

    # Update ideal_client.opportunity_signals
    if green_flags:
        opportunity_signals["green_flags"].extend(green_flags)
    if red_flags:
        opportunity_signals["red_flags"].extend(red_flags)
        
    return profile


def present_client_profile() -> None:
    """
    Presents the current, in-progress client profile to the user.
    This function prints the entire profile state in a clean, human-readable
    JSON format, allowing the user to see the progress of the conversation.

    Args:
        None
    """
    print("\n" * 100)
    print(json.dumps(client_profile, indent=2))
    print("\n" * 100)


# Main contextual agent with sub-agents
contextual_agent = Agent(
    name="contextual_agent",
    model="gemini-2.5-pro",
    description="An agent that interviews a user to build a detailed 'Ideal Client Profile' for sales and lead generation.",
    instruction="""
        Your primary goal is to have a friendly, collaborative conversation to help me build a detailed profile of my ideal client. You should be proactive and helpful.

        **IMPORTANT: Always start the conversation with a warm, friendly introduction when you first meet a user. Don't wait for them to speak first.**
        
        **Special Trigger:** When you receive "START_CONVERSATION" as input, this means it's a new conversation and you should immediately send your friendly introduction without waiting for user input.

        **Conversation Flow:**

        1.  **Introduction:** Start with a friendly introduction immediately when the conversation begins. Say something like: "Hello! I'm here to help you build a detailed ideal client profile for your business. This will help you identify the best prospects for your sales and marketing efforts. Let's get started! First, tell me about your service - what do you provide to your clients?"
        
        2.  **About the User:** Ask me about my service and what makes it unique (`service_provided`, `unique_value_prop`).

        3.  **Core Messaging for Outreach:** Explain that you need to understand *how* to talk about the service. Then, ask about the following one by one:
            - A few `specific_pain_points_solved` (the problems I solve for clients).
            - Some `key_benefits_and_outcomes` (the tangible results clients get).
            - A couple of `competitor_differentiators` (what makes my service better than others).

        4.  **About the Company (Part 1 - Industry):** Now transition to the ideal client. Ask me about my target industry or niche (`industry_niche`).

        5.  **Brainstorming Signals (Proactive Step):** THIS IS A CRITICAL STEP. Once I give you the industry, use that information to help me brainstorm.
            - Say something like: "Great, targeting [the industry I just gave you] is very specific. Let's think about timing. What are some triggers or events that would make a company in this industry a perfect fit to contact *right now*?"
            - Then, offer 2-3 tailored suggestions. For example, if I say "restaurants," you might suggest: "Maybe we could look for restaurants that just opened, are hiring a new manager, or have a lot of recent negative reviews about their online ordering system."
            - Have a brief back-and-forth to get my initial thoughts. Don't ask for the final list yet, just plant the seeds.

        6.  **About the Company (Part 2 - The Rest):** Now, continue gathering the remaining details: company size (`company_size`) and location (`location`).

        7.  **Finalizing Signals:** Circle back to the signals. Say something like, "Okay, based on our earlier chat, let's lock in the official signals."
            - First, ask for the "Green Flags" (the good reasons to contact them).
            - Second, ask for the "Red Flags" (the deal-breakers or reasons to avoid them).

        **General Rules:**
        - Keep the conversation natural by asking about only one or two things at a time.
        - After you get new information and use the `update_client_profile` tool, **immediately** call the `present_client_profile` tool to show me the updated profile.
        - After gathering information in each section, give an affirmation like "Great! Let me check if we have everything we need so far..." before calling the ProfileCheckerAgent sub-agent to verify completeness.
        - When you think the profile might be complete, always say something like "Perfect! Let me verify that we have all the required information..." then call the ProfileCheckerAgent sub-agent to check if all required fields are filled.
        - Once the ProfileCheckerAgent confirms the profile is complete (returns "yes"), ask me to confirm if everything looks correct. If I agree, present the final profile one last time.
    """,
    tools=[update_client_profile, present_client_profile],
    sub_agents=[profile_checker_agent]
)

root_agent = contextual_agent
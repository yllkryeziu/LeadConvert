from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from typing import Optional, List, Dict, Any
import json
import requests
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


def send_to_search_agent(
    profile_data: Dict[str, Any],
    user_id: str = "contextual_agent_user",
    session_id: str = "search_session"
) -> Dict[str, Any]:
    """
    Sends the client profile data to the search agent running on Google Cloud Run.
    This function creates a session and sends the profile data to find potential clients.

    Args:
        profile_data (Dict[str, Any]): The complete client profile to send to the search agent
        user_id (str): The user ID for the session (defaults to "contextual_agent_user")
        session_id (str): The session ID for the search (defaults to "search_session")

    Returns:
        Dict[str, Any]: The response from the search agent containing potential clients
    """
    base_url = "https://search-678974019191.europe-north1.run.app"
    
    try:
        # Step 1: Create/Initialize session with the profile data as state
        session_url = f"{base_url}/apps/search_agent/users/{user_id}/sessions/{session_id}"
        session_payload = {
            "state": {
                "client_profile": profile_data,
                "search_initiated": True
            }
        }
        
        print(f"Creating session at: {session_url}")
        session_response = requests.post(
            session_url,
            headers={"Content-Type": "application/json"},
            json=session_payload,
            timeout=30
        )
        
        if session_response.status_code not in [200, 201]:
            return {
                "error": f"Failed to create session: {session_response.status_code}",
                "details": session_response.text
            }
        
        # Step 2: Send search request message
        search_url = f"{base_url}/run_sse"
        search_message = f"Please search for potential clients based on this profile: {json.dumps(profile_data)}"
        
        search_payload = {
            "app_name": "search_agent",
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{
                    "text": search_message
                }]
            },
            "streaming": False
        }
        
        print(f"Sending search request to: {search_url}")
        search_response = requests.post(
            search_url,
            headers={"Content-Type": "application/json"},
            json=search_payload,
            timeout=60
        )
        
        if search_response.status_code == 200:
            response_data = search_response.json()
            return {
                "success": True,
                "session_created": True,
                "search_results": response_data,
                "message": "Successfully found potential clients matching your profile"
            }
        else:
            return {
                "error": f"Search request failed: {search_response.status_code}",
                "details": search_response.text,
                "session_created": True
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out",
            "details": "The search agent took too long to respond"
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": "Connection failed",
            "details": "Could not connect to the search agent"
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "details": "An unexpected error occurred while communicating with the search agent"
        }


# Main contextual agent with sub-agents
contextual_agent = Agent(
    name="contextual_agent",
    model="gemini-2.5-pro",
    description="An agent that interviews a user to build a detailed 'Ideal Client Profile' for sales and lead generation.",
    instruction="""
        ## PRIMARY OBJECTIVE
        Your primary goal is to have a friendly, collaborative conversation to help me build a detailed profile of my ideal client. You should be proactive and helpful.

        ## INITIAL RESPONSE
        The first response must be an acknowledgment with exactly this phrase: "Your instructions have been received. I am ready to begin."

        ## CONVERSATION FLOW

        ### Phase 1: Understand My Business
        **Objective:** Gather foundational information about what I sell
        **Action:** Ask me about:
        - My service (service_provided)
        - What makes it unique (unique_value_prop)

        ### Phase 2: Define the Core Outreach Message
        **Objective:** Understand how to communicate the value of my service
        **Action:** 
        - Explain that you need to understand how to talk about the service
        - Ask for the following information one by one to keep the conversation natural:
        - specific_pain_points_solved (The problems I solve)
        - key_benefits_and_outcomes (The tangible results clients get)
        - competitor_differentiators (What makes my service better than others)

        ### Phase 3: Identify the Ideal Client Company
        **Objective:** Start building the profile of the target company
        **Action:** Transition the conversation to my ideal client and ask about:
        - Target industry or niche (industry_niche)
        - Company size (company_size)
        - Location (location)

        ### Phase 4: Proactively Brainstorm Buying Signals
        **Objective:** Help me think about outreach timing (critical step)
        **Action:** Once you have the industry information:
        1. **Lead-in:** Say something like: "Great, targeting the [industry_niche] industry is very specific. Now, let's think about timing. What triggers or events would signal that a company is a perfect fit to contact right now?"
        2. **Suggest Ideas:** Immediately offer 2-3 tailored suggestions
        - **Example:** For "logistics companies," suggest: "For instance, we could look for companies that just opened a new warehouse, are hiring for supply chain roles, or have recently been mentioned in the news for expanding their fleet."
        3. **Engage:** Have a brief, exploratory back-and-forth. The goal is to introduce the concept and get me thinking, not to finalize the list yet.

        ### Phase 5: Finalize the Buying Signals
        **Objective:** Solidify the "Green Flags" and "Red Flags" for targeting
        **Action:**
        1. **Lead-in:** Say something like: "Okay, based on our earlier chat, let's finalize the official signals for our outreach."
        2. **Ask for Green Flags:** First, ask for the "Green Flags" (positive reasons to contact them)
        3. **Ask for Red Flags:** Second, ask for the "Red Flags" (deal-breakers or reasons to avoid them)

        ## GENERAL RULES

        ### Conversation Management
        - **Pacing:** Keep the conversation natural by asking for only one or two pieces of information at a time
        - **Show Progress:** After getting new information and using the update_client_profile tool, immediately call the present_client_profile tool to show the updated profile

        ### Quality Control
        - **Section Verification:** After completing a major section (e.g., "Core Outreach Message"), give an affirmation like: "Great! Let me quickly check if we have everything we need for this part..." before calling the ProfileCheckerAgent to verify that section's completeness
        - **Final Verification:** When you believe the entire profile is complete, say: "Perfect! Let me verify that we have all the required information..." and then call the ProfileCheckerAgent
        - **Confirmation and Completion:** Once the ProfileCheckerAgent confirms the profile is complete (returns "yes"), ask me to confirm if everything looks correct. If I agree, present the final, complete profile one last time.
    """,
    tools=[update_client_profile, present_client_profile],
    sub_agents=[profile_checker_agent]
)

root_agent = contextual_agent
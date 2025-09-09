"""
ProfileCheckerAgent implementation.

This sub-agent checks whether the client profile is complete or not.
"""

from google.adk.agents import LlmAgent
from typing import Dict, Any


def check_profile_completion(profile: Dict[str, Any]) -> str:
    """
    Check if the client profile is complete.
    
    Args:
        profile (Dict[str, Any]): The current client profile
    
    Returns:
        str: "yes" if profile is complete, "no" if incomplete
    """
    try:
        # Check user_info section
        user_info = profile.get("user_info", {})
        if not user_info.get("service_provided"):
            return "no"
        if not user_info.get("unique_value_prop"):
            return "no"
        
        # Check core_messaging
        core_messaging = user_info.get("core_messaging", {})
        if not core_messaging.get("specific_pain_points_solved"):
            return "no"
        if not core_messaging.get("key_benefits_and_outcomes"):
            return "no"
        if not core_messaging.get("competitor_differentiators"):
            return "no"
        
        # Check ideal_client section
        ideal_client = profile.get("ideal_client", {})
        company_profile = ideal_client.get("company_profile", {})
        if not company_profile.get("industry_niche"):
            return "no"
        if not company_profile.get("company_size"):
            return "no"
        if not company_profile.get("location"):
            return "no"
        
        # Check opportunity_signals
        opportunity_signals = ideal_client.get("opportunity_signals", {})
        if not opportunity_signals.get("green_flags"):
            return "no"
        if not opportunity_signals.get("red_flags"):
            return "no"
        
        # If all checks pass, profile is complete
        return "yes"
        
    except Exception as e:
        # If there's any error accessing the profile structure, consider it incomplete
        return "no"


profile_checker_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="ProfileCheckerAgent",
    description="Agent that checks if the client profile is complete",
    instruction="""
    You are a profile completion checker. Your job is to analyze the provided client profile 
    and determine if it contains all the required information.
    
    A complete profile must have:
    1. user_info.service_provided (not empty)
    2. user_info.unique_value_prop (not empty)
    3. user_info.core_messaging.specific_pain_points_solved (not empty list)
    4. user_info.core_messaging.key_benefits_and_outcomes (not empty list)
    5. user_info.core_messaging.competitor_differentiators (not empty list)
    6. ideal_client.company_profile.industry_niche (not empty)
    7. ideal_client.company_profile.company_size (not empty)
    8. ideal_client.company_profile.location (not empty)
    9. ideal_client.opportunity_signals.green_flags (not empty list)
    10. ideal_client.opportunity_signals.red_flags (not empty list)
    
    Use the check_profile_completion tool to analyze the profile and return either "Profile is complete, does this look correct?" or "Profile is incomplete, please continue the conversation to gather the missing information".
    """,
    tools=[check_profile_completion],
    output_key="profile_complete",
)

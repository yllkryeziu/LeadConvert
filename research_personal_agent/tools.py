import json
import os
import re
import logging
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
logging.basicConfig(level=logging.INFO)

def extract_contacts(company_name: str) -> str:
    """Extract contact emails and phone numbers for a company."""
    results = tavily_client.search(query=f"{company_name} contact page", max_results=3)
    html = "".join(r.get("content", "") + "\n" for r in results.get("results", []))
    emails = re.findall(r"[\\w\\.-]+@[\\w\\.-]+\\.[A-Za-z]{2,}", html)
    phones = re.findall(r"\\+?\\d[\\d\\s\\-()]{7,}", html)
    data = {"emails": list(dict.fromkeys(emails))[:3],
            "phone_numbers": list(dict.fromkeys(phones))[:3]}
    return json.dumps(data)

def perform_research(company_name: str) -> str:
    """Gather mission, values, news summaries for a company."""
    queries = [f"{company_name} mission and values",
               f"{company_name} recent news and press releases",
               f"{company_name} email id and phone number"]
    content = ""
    for q in queries:
        res = tavily_client.search(query=q, max_results=3)
        for r in res.get("results", []):
            content += r.get("content", "") + "\n\n"
    return json.dumps({"research_text": content})

def build_persona(input_json: str) -> str:
    """Generate a persona summary from research text and contacts."""
    data = json.loads(input_json)
    persona = {
        "company": data.get("company_name"),
        "key_traits": "Innovative, Privacy-focused, Customer-centric",
        "pain_points": "Integration complexity, Data security",
        "tone": "Formal and detailed"
    }
    return json.dumps(persona)

def draft_email(input_json: str) -> str:
    """Draft an email pitch using persona and contacts."""
    data = json.loads(input_json)
    company = data["persona"]["company"]
    traits = data["persona"]["key_traits"]
    pain = data["persona"]["pain_points"]
    subject = f"Partnership Opportunity with {company}"
    body = (
        f"Hello {company} team,\n\n"
        f"Your focus on {traits} aligns perfectly with our solutions. "
        f"We understand challenges around {pain} and can help by ...\n\n"
        f"Best regards,\nYour Name"
    )
    return json.dumps({"subject": subject, "body": body})

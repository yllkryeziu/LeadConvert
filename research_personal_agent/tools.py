import json
import os
import re
import logging
# from tavily import TavilyClient
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set")

# tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
logging.basicConfig(level=logging.INFO)

# def extract_contacts(company_name: str) -> str:
#     """Extract contact emails and phone numbers for a company.

#     Query strategy:
#     - Prefer the official contact page and support pages
#     - Fall back to press/newsroom and LinkedIn if needed
#     - Use company name disambiguation terms
#     """
#     queries = [
#         f"{company_name} official site contact email phone",
#         f"{company_name} contact page site:*.{company_name.split()[0].lower()}.*",
#         f"{company_name} support email site:*.{company_name.split()[0].lower()}.*",
#         f"{company_name} press newsroom contact",
#         f"{company_name} LinkedIn company page contact"
#     ]
#     results = {"results": []}
#     for q in queries:
#         res = tavily_client.search(query=q, max_results=3)
#         results["results"].extend(res.get("results", []))
#     html = "".join(r.get("content", "") + "\n" for r in results.get("results", []))
#     emails = re.findall(r"[\\w\\.-]+@[\\w\\.-]+\\.[A-Za-z]{2,}", html)
#     phones = re.findall(r"\\+?\\d[\\d\\s\\-()]{7,}", html)
#     data = {"emails": list(dict.fromkeys(emails))[:3],
#             "phone_numbers": list(dict.fromkeys(phones))[:3]}
#     return json.dumps(data)

# def perform_research(company_name: str) -> str:
#     """Gather mission, values, news summaries for a company.

#     Query strategy:
#     - Official about/mission, product pages, leadership page
#     - Press/newsroom for recent updates
#     - Funding or milestone announcements
#     - Careers page to infer scale and functions
#     """
#     queries = [
#         f"{company_name} site:about.* OR site:*/*about* mission values",
#         f"{company_name} site:*/*press* OR site:*/*news* recent press releases",
#         f"{company_name} product platform overview site:*/*product*",
#         f"{company_name} contact number",
#         f"{company_name} contact email",
#         f"{company_name} leadership team site:*/*leadership*",
#         f"{company_name} careers hiring site:*/*careers*",
#     ]
#     content = ""
#     for q in queries:
#         res = tavily_client.search(query=q, max_results=3)
#         for r in res.get("results", []):
#             content += r.get("content", "") + "\n\n"
#     return json.dumps({"research_text": content})

def build_persona(input_json: str) -> str:
    """Generate a persona summary from research text and contacts.

    Inputs JSON should include: company_name, contacts{{emails, phone_numbers}}, research.
    """
    data = json.loads(input_json)
    persona = {
        "company": data.get("company_name"),
        "key_traits": "Innovative, Privacy-focused, Customer-centric",
        "pain_points": "Integration complexity, Data security",
        "tone": "Formal and detailed"
    }
    return json.dumps(persona)

def draft_email(input_json: str) -> str:
    """Draft an email pitch using persona and contacts.

    Inputs JSON should include: persona, contacts, user_context, company_name.
    """
    data = json.loads(input_json)
    company = data.get("company_name") or data["persona"].get("company")
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


def send_email(receiver_email: str, receiver_name: str, subject: str, content: str) -> str:
    """Send an email via SMTP.

    Requires EMAIL_USER and EMAIL_PASSWORD in environment variables.
    Returns JSON with status and optional error message.
    """
    print("Starting mail senfing process...")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_name = os.getenv("EMAIL_NAME", "Noreply Smart Assistant")

    if not email_user or not email_password:
        return json.dumps({
            "status": "error",
            "error": "Missing EMAIL_USER or EMAIL_PASSWORD in environment"
        })

    message = MIMEMultipart()
    message['From'] = f'"{email_name}" <{email_user}>'
    message['To'] = f'"{receiver_name}" <{receiver_email}>'
    message['Subject'] = subject
    message.attach(MIMEText(content, 'plain'))

    print("Sending mail to:", receiver_email)
    print("Content of message:", content)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(message)
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
    finally:
        try:
            server.quit()
        except Exception:
            pass

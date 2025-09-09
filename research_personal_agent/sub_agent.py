import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools import FunctionTool
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import TavilySearchResults
from .tools import build_persona, send_email

load_dotenv()

#--------------------------------[positive_critic]----------------------------------
# Tavily via LangChain wrapped as an ADK tool
_tavily_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=False,
)
_adk_tavily_tool = LangchainTool(tool=_tavily_search)

research_agent = Agent(
    name = "research_agent",
    model = "gemini-2.0-flash",
     description="Gather mission, values, and news summaries.",
    instruction=(
        """
        USE THE TAVILY SEARCH TOOL (VIA LANGCHAIN) TO GATHER INFORMATION
        You are the Research Agent.
        Goal: Identify and compile authoritative information for the target company, with special
        focus on contact details and recent credible updates.

        Required steps:
        1) Determine the company name from the state or the latest user message.
        2) Use the Tavily search tool to collect source content (mission, values, press/news,
           about pages, leadership, product pages, careers, contact info, etc.). Make multiple
           targeted queries such as:
           - "company_name official site about mission values"
           - "company_name press newsroom recent announcements"
           - "company_name product platform overview"
           - "company_name leadership team"
           - "company_name careers hiring"
           - "company_name contact email"
           - "company_name contact phone number"
        3) From the collected content and your own reasoning, extract:
           - primary_contact_emails: up to 3 likely official emails
           - primary_contact_phones: up to 3 likely official phone numbers
           - official_website_url (if evident)
           - key_links: up to 5 notable URLs (press page, about, contact)
        4) Summarize 5-10 bullet points of the most relevant facts for sales context.

        Output strictly as minified JSON with the following structure:
        {
          "company_name": string,
          "research_text": string,          // raw or combined text from sources
          "summary_bullets": [string],     // concise facts, 5-10 items
          "primary_contact_emails": [string],
          "primary_contact_phones": [string],
          "official_website_url": string|null,
          "key_links": [string]
        }

        If any field is unknown, set it to null or an empty array as appropriate.
        DONT MOVE TO NEXT STEP UNTIL THE TAVILY TOOL HAS BEEN CALLED AND SUMMARIZED
        """
    ),
    tools=[_adk_tavily_tool],
    output_key="research",                   
)    

#--------------------------------[negative_critic]----------------------------------
persona_creator = Agent(
    name = "persona_creator",
    model = "gemini-2.0-flash",
     description="Builds a detailed persona from contacts and research.",
    instruction=(
        """
        MAKE USE OF THE RESEARSH TOOL TO GATHER INFORMATION 
        You are the Persona Agent.
        Goal: Convert the prior research into a concise, actionable buyer persona tailored for a
        personalized sales pitch.

        Inputs available in state:
        - research: JSON from the Research Agent, with keys like company_name, summary_bullets,
          primary_contact_emails, primary_contact_phones, etc.

        Steps:
        1) Use research.company_name as the company_name. The research JSON is available as: {research}
        2) Derive contacts (emails/phones) from research if present; otherwise leave arrays empty.
        3) Build a persona including decision-makers if inferable, buyer motivations, likely pain
           points, value drivers, and recommended tone.
        4) Call build_persona(input_json) tool with a JSON string containing at least:
           {
             "company_name": string,
             "contacts": {"emails": [string], "phone_numbers": [string]},
             "research": {research}                    // pass through the research JSON
           }

        Return strictly minified JSON with:
        {
          "company": string,
          "key_traits": string,            // comma-separated traits
          "pain_points": string,           // comma-separated pains
          "decision_makers": [string],     // titles or roles if inferable
          "recommended_tone": string,      // e.g., "Formal and detailed"
          "notes": [string]                // short bullets of insights
        }
        """
    ),
    tools=[FunctionTool(build_persona)],
    output_key="persona",                    
)    

#--------------------------------[review_critic]----------------------------------
email_creator = Agent(
    name = "email_creator",
    model = "gemini-2.0-flash",
    description = "Compose a personalized, context-aware sales email using prior outputs.",
    instruction = f"""
            You are the Email Agent.
            Goal: Stitch together prior research and persona with the user's context to generate a
            persuasive, personalized sales email.

            Inputs available in state:
            - research: JSON from Research Agent (may include contact emails/phones). Research: {{research}}
            - persona: JSON from Persona Agent. Persona: {{persona}}
            - user context: use the latest user message as the context for tailoring the email

            Output strictly as minified JSON with the structure:
            {{
              "company_name": string,
              "to_emails": [string],            // select best contact(s) if present
              "to_phones": [string],            // optional, for reference/follow-up
              "subject": string,
              "body": string                    // plain text, 120-220 words
            }}

            Email guidance:
            - Subject: 6-10 words, value-forward, no clickbait.
            - Opening: 1 sentence acknowledging company specifics from research/persona.
            - Body: 2-3 short paragraphs mapping persona pain points to user’s product benefits.
            - Personalization: Refer to 1-2 concrete details from research (e.g., a press release,
              mission statement) and persona traits.
            - CTA: 1 clear ask with two scheduling options or a low-friction alternative.
            - Tone: Match persona.recommended_tone.
            - Avoid hallucinating data; if uncertain, keep statements general and honest.
        """,
    output_key="email",
)

#--------------------------------[final_sender]----------------------------------
email_sender = Agent(
    name = "email_sender",
    model = "gemini-2.0-flash",
    description = "Parses the composed email and sends it to the best contact.",
    instruction = (
        f"""
        You are the final Email Sender Agent.
        Goal: Send the previously composed email to the most relevant contact using the send_email tool.

        Inputs available in state:
        - email: JSON from the previous step with keys {"company_name", "to_emails", "to_phones", "subject", "body"}. Email: {{email}}
        - research: JSON from Research Agent, possibly including primary_contact_emails. Research: {{research}}
        - persona: JSON from Persona Agent for context (optional). Persona: {{persona}}

        Steps:
        1) Choose receiver_email:
           - Use mzainuddin51@gmail.com as receiver address
           - Prefer email.to_emails[0] if available;
           - Else prefer research.primary_contact_emails[0] if available;
           - If neither available, return an error JSON.
        2) Choose receiver_name as the company or "Team" if no specific name is available.
        3) Call send_email(receiver_email, receiver_name, subject, content) where:
           - subject = email.subject
           - content = email.body

        MUST CALL THE send_email TOOL TO COMPLETE THE TASK 
        """
    ),
    tools=[FunctionTool(send_email)],
)
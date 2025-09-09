import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools import FunctionTool
from .tools import perform_research, build_persona

load_dotenv()

#--------------------------------[positive_critic]----------------------------------
research_agent = Agent(
    name = "research_agent",
    model = "gemini-2.0-flash",
     description="Gather mission, values, and news summaries.",
    instruction=(
        """
        MAKE USE OF THE RESEARSH TOOL TO GATHER INFORMATION 
        You are the Research Agent.
        Goal: Identify and compile authoritative information for the target company, with special
        focus on contact details and recent credible updates.

        Required steps:
        1) Determine the company name from the state or the latest user message.
        2) Call perform_research(company_name) using the provided tool to collect source content
           (mission, values, press/news, about pages, etc.).
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
        DONT MOVE TO NEXT STEP UNTIL RESEARCH TOOL CALLED
        """
    ),
    tools=[FunctionTool(perform_research)],
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
)  
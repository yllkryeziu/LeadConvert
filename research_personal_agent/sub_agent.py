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
        "Call tool_perform_research(company_name=(Gather this information from what context was passed)) and return the output."
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
        "Call tool_build_persona(company_name=(from context information), contacts=(from context info)"
        "research=\"{research}\") and return the output."
    ),
    tools=[FunctionTool(build_persona)],
    output_key="persona",                    
)    

#--------------------------------[review_critic]----------------------------------
email_creator = Agent(
    name = "email_creator",
    model = "gemini-2.0-flash",
    description = "An agent that reviews the positive and negative aspects of a user's question and summarizes it overall.",
    instruction = f"""
            You are an agent who provides and stiches all information from previous agents. 
            * Research info ```{{research}}```  
            * Persona created: ```{{persona}}```

           Looking at this information. return a json output that stiches information in a json with: 
           1. Company Name
           2. Contact number if found
           3. Email Id if found
           4. Personal Email to be sent based on context of user requirements. 

           Make sure the mail is well tailored according to the persona and previosu information gathered. 
   
        """,
)  
from dotenv import load_dotenv
from google.adk.agents import SequentialAgent

from .sub_agent import persona_creator, research_agent, email_creator, email_sender

load_dotenv()

# `root_agent` defines a simple pipeline where each sub-agent runs in order.
# Use SequentialAgent when later steps depend on outputs produced by earlier steps.
# In this pipeline:
#  - `positive_critic` runs first to provide a positive critique,
#  - `negative_critic` runs next to provide a negative critique,
#  - `review_critic` runs last to review combined outputs and produce a final evaluation.
root_agent = SequentialAgent(
    name="pipeline_agent",
    sub_agents=[research_agent, persona_creator, email_creator, email_sender],
    description="This is an agent that sequentially executes agents(research_agent, persona_creator, email_creator, email_sender)"
)
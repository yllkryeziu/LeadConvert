"""
Configuration for the Contextual Agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_CONTEXTUAL_AGENT_URL = "http://localhost:8080"
DEFAULT_UI_CLIENT_URL = os.getenv("UI_CLIENT_URL", "http://localhost:3000")

# Model configuration
MODEL = os.getenv("MODEL", "gemini-2.5-pro")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
TOP_P = float(os.getenv("TOP_P", "0.95"))
TOP_K = int(os.getenv("TOP_K", "40"))


from sub_agents import search_agent
metadatas = search_agent.process_context_data({
    "user_info": {
        "service_provided": "building and optimizing high-end Shopify e-commerce websites",
        "unique_value_prop": "Creating a premium, luxury user experience that is proven to increase conversion rates for exclusive brands.",
        "core_messaging": {
            "specific_pain_points_solved": [
                "a slow, clunky website that frustrates users",
                "a confusing checkout process that leads to high cart abandonment",
                "a generic site design that fails to communicate their premium brand identity"
            ],
            "key_benefits_and_outcomes": [
                "a much faster and more beautiful website",
                "a measurable increase in online sales, typically around 15-20%",
                "a stronger, more professional brand image"
            ],
            "competitor_differentiators": [
                "a fully bespoke design tailored to each client, unlike agencies that use templates",
                "includes 3 months of post-launch performance monitoring and optimization"
            ]
        }
    },
    "ideal_client": {
        "company_profile": {
            "industry_niche": "Direct-to-consumer (DTC) industry, specifically focusing on niches like independent fashion labels and high-end consumer goods.",
            "company_size": "5 to 30 employees",
            "location": "North America (USA and Canada)"
        },
        "opportunity_signals": {
            "green_flags": [
                "brand gets a feature in a major publication (e.g., Vogue)",
                "hiring for a new marketing position",
                "current website has a low score on Google PageSpeed Insights"
            ],
            "red_flags": [
                "brands that sell most of their products on Amazon",
                "companies that have had recent public layoffs",
                "business has been operating for less than a year"
            ]
        }
    }
})

print(metadatas)
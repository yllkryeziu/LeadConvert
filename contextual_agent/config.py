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

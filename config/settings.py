import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID", "")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "fitness_data.db")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

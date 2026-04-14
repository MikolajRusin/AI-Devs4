import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience dependency
    def load_dotenv():
        return False

load_dotenv()

AI_DEVS_HUB_API_KEY = os.getenv('AI_DEVS_HUB_API_KEY')
AI_DEVS_HUB_BASE_URL = os.getenv('HUB_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

AGENT_MODEL = 'gpt-4.1-mini-2025-04-14'

TASK = 'windpower'
VERIFY_URL = f'{AI_DEVS_HUB_BASE_URL}/verify'

RATED_POWER_KW = 14
CUTOFF_WIND_MS = 14
MIN_WIND_MS = 4
STORM_RESET_HOURS = 1

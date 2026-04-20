from dotenv import load_dotenv
import os

load_dotenv()
AI_DEVS_HUB_API_KEY  = os.getenv('AI_DEVS_HUB_API_KEY')
AI_DEVS_HUB_BASE_URL = os.getenv('HUB_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

MODEL = 'gpt-4.1-mini-2025-04-14'

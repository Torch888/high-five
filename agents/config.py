import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIG = {
    "config_list": [
        {
            "model": "google/gemini-2.0-flash-001",
            "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
            "base_url": "https://openrouter.ai/api/v1",
            "api_type": "openai",
        }
    ],
    "temperature": 0.7,
}

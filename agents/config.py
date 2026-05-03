import os
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(key, "")
        except Exception:
            pass
    return val

def get_llm_config() -> dict:
    return {
        "config_list": [
            {
                "model": "google/gemini-2.5-flash",
                "api_key": _get_secret("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1",
                "api_type": "openai",
            }
        ],
        "temperature": 0.7,
    }

LLM_CONFIG = None  # use get_llm_config() at call time

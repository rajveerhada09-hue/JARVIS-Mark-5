"""
PROJECT : JARVIS MARK 5

FILE : providers.py

PATH : utils/providers.py
"""

import os
import requests
from dotenv import load_dotenv

from utils.config import CONFIG

load_dotenv()


def _normalize_provider(value):
    return (value or "").strip().lower()


def _get_provider_setting(key, default):
    env_value = os.getenv(key)
    if env_value:
        return _normalize_provider(env_value)

    config_value = None
    if isinstance(CONFIG, dict):
        config_value = CONFIG.get(key) or CONFIG.get(key.lower()) or CONFIG.get(key.replace("_", "").lower())
    return _normalize_provider(config_value or default)


PRIMARY_LLM = _get_provider_setting("PRIMARY_LLM", "gemini")
BACKUP_LLM = _get_provider_setting("BACKUP_LLM", "openai")
FAST_LLM = _get_provider_setting("FAST_LLM", "groq")

SEARCH_PROVIDER = _get_provider_setting("SEARCH_PROVIDER", "tavily")
RESEARCH_PROVIDER = _get_provider_setting("RESEARCH_PROVIDER", "tavily")


def get_primary_llm():
    return PRIMARY_LLM


def get_backup_llm():
    return BACKUP_LLM


def get_fast_llm():
    return FAST_LLM


def get_search_provider():
    return SEARCH_PROVIDER


def get_research_provider():
    return RESEARCH_PROVIDER


def call_llm_provider(provider, prompt, *, system_prompt="", temperature=0.7, timeout=45):
    provider = _normalize_provider(provider)

    if provider in {"openai", "gpt", "chatgpt"}:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are JARVIS."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            }
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content else None
        except Exception:
            return None

    if provider in {"gemini", "google"}:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
            return text.strip() if text else None
        except Exception:
            return None

    if provider in {"groq", "llama", "mixtral"}:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        try:
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are JARVIS."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            }
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content else None
        except Exception:
            return None

    return None


def build_provider_client(provider):
    provider = _normalize_provider(provider)
    if provider in {"gemini", "google"}:
        try:
            from google import genai

            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                return genai.Client(api_key=api_key)
        except Exception:
            return None
    return None
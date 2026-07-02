"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : test_apis.py

PATH    : test_apis.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from dotenv import load_dotenv
import os

load_dotenv()

print("=== API KEYS STATUS ===")
print("GEMINI_API_KEY     :", "✅ Present" if os.getenv("GEMINI_API_KEY") else "❌ Missing")
print("GROQ_API_KEY       :", "✅ Present" if os.getenv("GROQ_API_KEY") else "❌ Missing")
print("OPENAI_API_KEY     :", "✅ Present" if os.getenv("OPENAI_API_KEY") else "❌ Missing")
print("DEEPEEK_API_KEY    :", "✅ Present" if os.getenv("DEEPEEK_API_KEY") else "❌ Missing")

# Test Gemini (fastest for now)
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello in one word.")
    print("\n✅ Gemini Test:", response.text.strip())
except Exception as e:
    print("\n❌ Gemini Error:", e)
"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : vision.py

PATH    : vision\vision.py

PURPOSE :
        computer vision tasks.

LAST UPDATED :
2026-06-28

============================================================
"""

import pyautogui
import os
import requests
from PIL import Image
from dotenv import load_dotenv

from utils.providers import build_provider_client

load_dotenv()
client = build_provider_client("gemini")

# PHONE_SCREEN_URL: Ye wo URL hoga jo tera phone screen share karte waqt dega
PHONE_IP = "192.168.1.XX" # Apne phone ka IP yahan dalna
PHONE_SCREEN_URL = f"http://{PHONE_IP}:8080/shot.jpg" 

def capture_screen(source="laptop"):
    screenshot_path = "screen_view.png"
    
    if source == "mobile":
        # Mobile screen capture using IP Webcam or ScreenStream
        try:
            response = requests.get(PHONE_SCREEN_URL, timeout=5)
            with open(screenshot_path, 'wb') as f:
                f.write(response.content)
            print("[VISION] Mobile screen captured.")
        except Exception as e:
            print(f"[ERROR] Mobile connect nahi ho paya: {e}")
            return None
    else:
        # Laptop screen capture
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        print("[VISION] Laptop screen captured.")
        
    return screenshot_path

def analyze_any_screen(chat_session, source="laptop"):
    img_path = capture_screen(source)
    if not img_path:
        return "Sir, mobile connect nahi hai. Laptop screen dekhu?"

    img = Image.open(img_path)
    prompt = f"Analyze this {source} screen for Rajveer. Explain what's happening and end with 'Sir'."
    
    response = chat_session.send_message([prompt, img])
    os.remove(img_path)
    return response.text
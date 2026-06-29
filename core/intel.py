"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : intel.py

PATH    : core\intel.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import requests
import datetime
import os
import webbrowser
from colorama import Fore
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def log_intel(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{Fore.MAGENTA}[{timestamp}] [INTEL] {Fore.WHITE}{msg}")


# ==================================================
# WEATHER
# ==================================================
def get_weather(city=None):
    try:

        if not city:
            try:
                ip_data = requests.get(
                    "https://ipapi.co/json/",
                    timeout=5
                ).json()

                city = ip_data.get("city", "Indore")

            except:
                city = "Indore"

        log_intel(f"Fetching weather for {city}")

        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}"
            f"&appid={WEATHER_API_KEY}"
            f"&units=metric"
        )

        res = requests.get(url, timeout=5).json()

        if str(res.get("cod")) != "200":
            return f"Unable to fetch weather for {city}"

        temp = res["main"]["temp"]
        feels = res["main"]["feels_like"]
        desc = res["weather"][0]["description"]

        return (
            f"Current temperature in {city} is "
            f"{temp} degrees Celsius. "
            f"It feels like {feels} degrees with {desc}."
        )

    except Exception as e:
        log_intel(f"Weather Error: {e}")
        return "Weather service is currently unavailable."


# ==================================================
# NEWS
# ==================================================
def get_news(limit=3):

    try:

        log_intel("Fetching latest news")

        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?country=in"
            f"&apiKey={NEWS_API_KEY}"
        )

        res = requests.get(url, timeout=5).json()

        if res.get("status") != "ok":
            return "News service unavailable."

        articles = res.get("articles", [])[:limit]

        if not articles:
            return "No headlines available."

        headlines = []

        for article in articles:
            title = article.get("title")

            if title:
                headlines.append(title.split(" - ")[0])

        return "Top headlines: " + ". ".join(headlines)

    except Exception as e:
        log_intel(f"News Error: {e}")
        return "Unable to fetch news."


# ==================================================
# COMBINED BRIEFING
# ==================================================
def get_daily_briefing():

    weather = get_weather()
    news = get_news()

    return f"{weather} {news}"


# ==================================================
# WEB SEARCH
# ==================================================
def search_web(query):

    search_query = (
        query.lower()
        .replace("search", "")
        .strip()
    )

    if not search_query:
        return "Nothing to search."

    log_intel(f"Searching: {search_query}")

    webbrowser.open(
        f"https://www.google.com/search?q={search_query}"
    )

    return f"Searching Google for {search_query}"
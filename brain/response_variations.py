"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : response_variations.py
PATH    : core\response_variations.py

CHANGES vs original:
  1. Expanded confirm_variation() pool from 7 to 20 entries.
  2. Expanded opening_variation() pool from 4 to 13 entries.
  3. Added 14 new pools: search, ack, wait, listen, thanks, positive, error,
     goodbye, casual, stressed, mood_pos, humor, yes, no, maybe.
  4. Added quick(pool_name) function — primary interface for ConversationEngine.
  5. Original confirm_variation() and opening_variation() signatures preserved.
============================================================
"""

import random

# ─── Original pools (expanded) ────────────────────────────────────────────────
CONFIRMATIONS = [
    "Done", "Ho gaya", "Finished", "All set", "Ready", "Task complete",
    "Completed", "Kaam ho gaya", "Sorted", "Yeh kar diya", "Done Sir",
    "Done Boss", "Finished Sir", "All done Boss", "Set ho gaya",
    "Chaliye", "Ho gaya Sir", "Theek hai ho gaya", "Ready Rajveer",
    "Done. Kuch aur?",
]
OPENING_VARIATIONS = [
    "Opening", "Launching", "Starting", "Bringing up", "On it",
    "Khol raha hoon", "Abhi open karta hoon", "Launching now",
    "Starting up", "Chal raha hai", "Opening now", "Let me get that",
    "Ek second",
]

# ─── New pools ────────────────────────────────────────────────────────────────
SEARCHING = [
    "Searching.", "Dekh raha hoon.", "Mil jaayega.", "Looking it up.",
    "On it.", "Dhundh raha hoon.", "Just a sec.", "Checking.",
    "Finding it.", "Let me check.", "Searching now.", "Abhi check karta hoon.",
]
ACKS = [
    "Haan.", "Ji.", "Bilkul.", "Theek hai.", "Got it.", "Clear hai.",
    "Sahi hai.", "Noted.", "Understood.", "Samajh gaya.", "Sure.", "Yep.",
    "Copy that.", "Roger.", "Main sun raha hoon.", "Haan Boss.", "Haan Sir.",
    "Ji Rajveer.", "Clear.",
]
WAIT = [
    "Ek second.", "Ek minute.", "Just a moment.", "Coming up.",
    "Processing.", "Thoda wait.", "Almost there.", "Abhi karta hoon.",
    "Working on it.", "Give me a moment.", "Ruko.", "Dekh raha hoon.",
]
LISTENING = [
    "Haan Boss?", "Listening Sir.", "Bol.", "Haan?", "Suno raha hoon.",
    "Ready.", "Batao.", "Main yahan hoon.", "I'm here.", "Speak Sir.",
    "Ready Sir.", "Haan Rajveer?", "Bol Boss.", "Main ready hoon.",
]
THANKS = [
    "Always.", "My pleasure Sir.", "Anytime Boss.", "Koi baat nahi.",
    "Bas aise hi.", "Always here.", "No problem.", "Kabhi bhi.",
    "Happy to.", "Yahin hoon.", "Yeh toh banta hai.", "Kuch aur?",
]
POSITIVE = [
    "Excellent Sir.", "Nice work Boss.", "Well done.", "Sahi kiya.",
    "Bahut badhiya.", "Great.", "Solid.", "Perfect.", "Acha kiya.",
    "That's good to hear.", "Noted.", "Achi progress hai.",
    "Bahut acha.", "Keep going.", "Lag raha hai ban jaayega.",
]
ERROR_RESPONSES = [
    "Let's fix it.", "Traceback bhejiye.", "Dekh raha hoon.",
    "Kya error aa raha hai?", "Share karo full error.",
    "Dependency conflict lag raha hai.", "Ek second, check karta hoon.",
    "Fix hoga, ruko.", "Kaun si line pe crash hua?",
    "Stack trace dikh raha hai?", "Import error hai?",
    "Module missing lag raha hai.", "Environment check karte hain.",
]
GOODBYE = [
    "Take care Sir.", "Theek hai Boss.", "Alvida.",
    "Systems remain active.", "I'll keep things running.",
    "Main yahan rahunga.", "Anytime.", "See you Sir.",
    "Jaate rahe. Main monitoring karta rahunga.",
    "Systems active. Jab chaaho aana.", "Take care Rajveer.",
]
CASUAL = [
    "Sab theek chal raha hai.", "Systems nominal.", "Sab ready hai.",
    "Nothing critical.", "All clear.", "Chill hai Boss.",
    "Everything's good.", "Sab green hai.", "No alerts.",
    "Smooth sailing.", "All good here.", "Quiet for now.",
]
STRESSED = [
    "Samajh raha hoon. Ek kaam ek time pe karte hain.",
    "Chill karo. Main hoon yahan.",
    "Let's break it down. Kya issue hai pehle?",
    "Ruko, step by step karte hain.",
    "It'll work out. Batao kya problem hai.",
    "Overwhelmed? Normal hai. Ek cheez ek time.",
    "Deep breath. Phir batao kya tackle karna hai.",
]
MOOD_POS = [
    "Achha suna.", "Good to hear Boss.", "That's great.", "Mast hai.",
    "Solid.", "Let's keep it going.", "Acha hai Sir.", "Nice.",
    "Progress ho rahi hai.", "That's the way.", "Keep at it.",
]
HUMOR = [
    "Noted, Boss.", "Classic.", "Interesting choice.",
    "Main judge nahi kar raha.", "Sure, why not.",
    "Alright then.", "Bold move.", "Theek hai, aap bole to.",
    "As you wish.", "Aisa sirf main kar sakta hoon.",
]
YES_ANSWERS   = ["Haan.", "Ji haan.", "Bilkul.", "Yes.", "Confirmed.", "Correct."]
NO_ANSWERS    = ["Nahi.", "Ji nahi.", "Nope.", "Negative.", "Not yet."]
MAYBE_ANSWERS = ["Ho sakta hai.", "Possible hai.", "Dekh lenge.", "Maybe."]

_POOLS = {
    "confirm":  CONFIRMATIONS,     "open":     OPENING_VARIATIONS,
    "search":   SEARCHING,         "ack":      ACKS,
    "wait":     WAIT,              "listen":   LISTENING,
    "thanks":   THANKS,            "positive": POSITIVE,
    "error":    ERROR_RESPONSES,   "goodbye":  GOODBYE,
    "casual":   CASUAL,            "stressed": STRESSED,
    "mood_pos": MOOD_POS,          "humor":    HUMOR,
    "yes":      YES_ANSWERS,       "no":       NO_ANSWERS,
    "maybe":    MAYBE_ANSWERS,
}


# ── Original functions (signatures preserved) ─────────────────────────────────
def confirm_variation(base: str = "Done") -> str:
    """Original signature preserved."""
    v = random.choice(CONFIRMATIONS)
    if base and base.strip():
        if random.random() < 0.5:
            return f"{v}. {base}."
        return f"{base}."
    return f"{v}."


def opening_variation(url: str) -> str:
    """Original signature preserved."""
    v = random.choice(OPENING_VARIATIONS)
    return f"{v} {url}."


# ── New helper ────────────────────────────────────────────────────────────────
def quick(pool_name: str) -> str:
    """
    Return one random response from a named pool.
    Pools: confirm, open, search, ack, wait, listen, thanks,
           positive, error, goodbye, casual, stressed, mood_pos,
           humor, yes, no, maybe
    """
    return random.choice(_POOLS.get(pool_name, ACKS))
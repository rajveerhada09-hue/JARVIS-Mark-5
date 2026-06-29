"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : human_layer.py
PATH    : core\personality\human_layer.py

CHANGES vs original:
  1. Added _AI_PHRASES regex to strip all ChatGPT patterns from any text.
  2. Added 100+ natural short-response pools (RESPONSE_POOLS dict).
  3. Added quick() function for pool-based instant replies.
  4. Added showcase_introduction() for formal demo mode.
  5. Added is_showcase_trigger() pattern matcher.
  6. Added _clean_ai_phrases() as a module-level utility.
  7. Expanded _make_god_friendly() — opener/ending no longer repeat immediately.
  8. All original method signatures preserved (set_mode, enhance, add_emotion).
  9. No new imports that don't exist in requirements.
============================================================
"""

import random
import re
from typing import Optional

# ── AI phrase blacklist ────────────────────────────────────────────────────────
_AI_PHRASES = re.compile(
    r"(as an ai[,.]?|as a language model[,.]?|i('m| am) (just |only )?an ai[,.]?|"
    r"i('m| am) here to help[,.]?|how (may|can) i (assist|help) you( today)?[,.]?|"
    r"i (understand|appreciate) your frustration[,.]?|i (sincerely )?apologize[,.]?|"
    r"certainly[,!]? i('d| would) (be happy|love) to[,.]?|"
    r"of course[,!]? i('d| would) (be happy|love) to[,.]?|"
    r"great question[,!.]?|i hope this helps[,!.]?|"
    r"is there anything else i can (help|assist)[^?]*\?|"
    r"feel free to ask[,.]?|i('m| am) (designed|programmed|built|trained) to[,.]?|"
    r"as your (virtual |ai |digital )?assistant[,.]?)",
    re.IGNORECASE,
)

_SHOWCASE_PAT = re.compile(
    r"(show(ing)? (you|jarvis)|introduc|my (friend|father|mother|brother|sister|guest|family|dad|mom)|"
    r"someone wants to (see|meet)|meet jarvis|jarvis (meet|say hello)|presenting jarvis)",
    re.IGNORECASE,
)


def _clean_ai_phrases(text: str) -> str:
    cleaned = _AI_PHRASES.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


# ── 100+ Natural Response Pools ───────────────────────────────────────────────
CONFIRMATIONS = [
    "Done.", "Ho gaya.", "Finished.", "All set.", "Ready.",
    "Task complete.", "Completed.", "Kaam ho gaya.", "Sorted.",
    "Yeh kar diya.", "Done Sir.", "Done Boss.", "Finished Sir.",
    "All done Boss.", "Set ho gaya.", "Chaliye.", "Done. Kuch aur?",
    "Ready Rajveer.", "Ho gaya Sir.", "Theek hai, ho gaya.",
]
OPENING = [
    "Opening.", "Launching.", "Starting.", "Bringing it up.", "On it.",
    "Khol raha hoon.", "Abhi open karta hoon.", "Launching now.",
    "Starting up.", "Chal raha hai.", "Opening now.", "Let me get that.",
    "Ek second.",
]
SEARCHING = [
    "Searching.", "Dekh raha hoon.", "Mil jaayega.", "Looking it up.",
    "On it.", "Dhundh raha hoon.", "Just a sec.", "Checking.",
    "Finding it.", "Let me check.", "Searching now.", "Abhi check karta hoon.",
]
ACKS = [
    "Haan.", "Ji.", "Bilkul.", "Theek hai.", "Got it.",
    "Clear hai.", "Sahi hai.", "Noted.", "Understood.", "Samajh gaya.",
    "Sure.", "Yep.", "Copy that.", "Roger.", "Main sun raha hoon.",
    "Haan Boss.", "Haan Sir.", "Ji Rajveer.", "Clear.",
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

RESPONSE_POOLS = {
    "confirm":  CONFIRMATIONS, "open":     OPENING,     "search":   SEARCHING,
    "ack":      ACKS,          "wait":     WAIT,         "listen":   LISTENING,
    "thanks":   THANKS,        "positive": POSITIVE,     "error":    ERROR_RESPONSES,
    "goodbye":  GOODBYE,       "casual":   CASUAL,       "stressed": STRESSED,
    "mood_pos": MOOD_POS,      "humor":    HUMOR,
    "yes":      YES_ANSWERS,   "no":       NO_ANSWERS,   "maybe":    MAYBE_ANSWERS,
}


def quick_response(pool: str) -> str:
    """Return one random response from a named pool."""
    return random.choice(RESPONSE_POOLS.get(pool, ACKS))


# Keep old name for compatibility with any existing callers
quick = quick_response


# ── Main Class ────────────────────────────────────────────────────────────────
class HumanLayer:
    def __init__(self):
        self.mode = "friendly"
        self._last_address: Optional[str] = None
        self._last_opener:  Optional[str] = None

        # Original pools — kept for backward compatibility
        self.friendly_openers = [
            "Samajh gaya", "Theek hai", "Bilkul", "Understood",
            "Ye clear hai", "Dekh leta hoon", "Main dekhta hoon",
            "Yeh manage karte hain", "Sahi hai", "Ho jayega",
            "Chal raha hai", "Clear hai",
        ]
        self.friendly_endings = [
            "Aur kuch chahiye ho to batao.",
            "Ye main abhi check karta hoon.",
            "Aage badhna hai to batana.",
            "Main yahin hoon.",
            "Iss par nazar rakhta hoon.",
            "Bas bol dena.",
        ]
        self.casual_addons = [
            " Main dekh leta hoon.",
            " Ye theek hai.",
            " Aise hi continue karte hain.",
        ]
        self.professional_openers = [
            "Understood.", "Here's my take:", "Based on the details,",
            "Certainly,", "Noted.", "Right.",
        ]
        self.professional_endings = [
            "This is the most practical approach.",
            "Let me know if you need further clarification.",
            "I recommend going with this.",
        ]

    # ── Public API (all original signatures preserved) ─────────────────────
    def set_mode(self, mode: str) -> None:
        mode = mode.lower().strip()
        if mode in ("friendly", "professional", "admin"):
            self.mode = mode

    def get_mode(self) -> str:
        return self.mode

    def is_showcase_trigger(self, text: str) -> bool:
        return bool(_SHOWCASE_PAT.search(text))

    def enhance(self, text: str, metadata: dict = None) -> str:
        """Original signature preserved. AI phrases are now stripped first."""
        if not text or len(text.strip()) < 3:
            return text
        metadata = metadata or {}
        text = _clean_ai_phrases(text)
        if self.mode == "friendly":
            return self._make_god_friendly(text, metadata)
        elif self.mode == "professional":
            return self._make_professional(text)
        elif self.mode == "admin":
            return f"[SYSTEM] {text}"
        return text

    def add_emotion(self, text: str, emotion: str = "neutral") -> str:
        """Original method — unchanged."""
        emojis = {
            "happy": "😎", "excited": "🔥", "thinking": "🤔",
            "warning": "⚠️", "sad": "😔",
        }
        emoji = emojis.get(emotion, "")
        return f"{emoji} {text}" if emoji else text

    # ── Private methods ──────────────────────────────────────────────────────
    def _make_god_friendly(self, text: str, metadata: dict = None) -> str:
        """Original improved: opener/address no longer repeat immediately."""
        metadata  = metadata or {}
        address   = self._pick_address(metadata.get("last_address"))
        opener    = self._pick_opener(self.friendly_openers, self._last_opener)
        self._last_opener = opener

        word_count = len(text.split())
        if word_count <= 6:
            result = text
        else:
            result = f"{opener} {address}, {text.strip()}"

        if word_count > 4 and random.random() < 0.30:
            result += random.choice(self.casual_addons)

        if word_count > 15 and random.random() < 0.30:
            result += f"\n\n{random.choice(self.friendly_endings)}"

        return result

    def _make_professional(self, text: str) -> str:
        opener = self._pick_opener(self.professional_openers, self._last_opener)
        self._last_opener = opener
        ending = random.choice(self.professional_endings)
        return f"{opener} {text}\n\n{ending}"

    def _pick_address(self, last_from_metadata: Optional[str] = None) -> str:
        addresses = ["Sir", "Boss", "Rajveer"]
        last      = last_from_metadata or self._last_address
        choices   = [a for a in addresses if a != last]
        if not choices:
            choices = addresses
        chosen = random.choice(choices)
        self._last_address = chosen
        return chosen

    def _pick_opener(self, pool: list, last: Optional[str]) -> str:
        choices = [o for o in pool if o != last]
        if not choices:
            choices = pool
        return random.choice(choices)

    # ── Showcase intro (called from ConversationEngine) ──────────────────────
    def showcase_introduction(self) -> str:
        import datetime
        h      = datetime.datetime.now().hour
        period = "morning" if h < 12 else "afternoon" if h < 17 else "evening"
        intros = [
            (
                f"Good {period}. I'm J.A.R.V.I.S. — Just A Rather Very Intelligent System, Mark 5. "
                "Designed and engineered by Rajveer Singh Rajput. "
                "I handle voice commands, automation, memory, system monitoring, "
                "and natural conversation — all running locally. "
                "It's a pleasure to meet you."
            ),
            (
                f"Good {period}. I'm J.A.R.V.I.S., Rajveer's personal AI operating intelligence. "
                "Built for voice interaction, automation, real-time awareness, and long-term memory. "
                "Everything you see here was designed and engineered by Rajveer. How can I help?"
            ),
        ]
        return random.choice(intros)
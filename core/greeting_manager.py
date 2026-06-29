"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : greeting_manager.py
PATH    : core\greeting_manager.py

CHANGES vs original:
  1. Expanded greeting pools: 10 morning, 8 afternoon, 7 evening, 7 night variants.
  2. Added _RETURN pool for "I'm back" wake-up context.
  3. Added first-boot detection — cinematic intro runs ONCE only, never again.
  4. Added _load_last / _save_last to prevent exact greeting repetition.
  5. Added optional wisdom/quote injection (~15% on morning startup).
  6. Added return_greeting() shortcut function.
  7. Original time_aware_greeting(memory) signature 100% preserved.
============================================================
"""

import datetime
import json
import os
import random
from typing import Optional

# ── Wisdom pool ───────────────────────────────────────────────────────────────
_WISDOM = [
    "Bhagavad Gita reminds us — karm karo, phal ki chinta mat karo.",
    "Chanakya: 'Never reveal what you are planning next.'",
    "Arjun bhi confused tha battlefield pe. Phir bhi uth ke kaam karo.",
    "Richard Feynman: 'The first principle is that you must not fool yourself.'",
    "Mahabharata teaches — patience and preparation win over panic.",
    "Chanakya Neeti: Discipline aur consistency aapki sabse badi strength hai.",
    "Gita says — focus on the action, never the outcome.",
    "Donald Knuth: 'Premature optimization is the root of all evil.'",
    "Ramayana: Har mushkil mein bhi dharma ka raasta hota hai.",
    "Mahavir Phule: 'Education is the most powerful weapon.'",
]

# ── Greeting pools ────────────────────────────────────────────────────────────
_MORNING = [
    "Good morning {addr}. Everything is operational.",
    "Good morning {addr}. Systems are ready.",
    "Morning {addr}. Ready when you are.",
    "Good morning {addr}. All modules online.",
    "Good morning {addr}. Hope you slept well. Systems are up.",
    "Morning {addr}. Nothing critical overnight. Let's go.",
    "Good morning {addr}. What are we working on today?",
    "Good morning {addr}. Coffee ya seedha kaam?",
    "Morning {addr}. All clear. Let's make it count.",
    "Good morning {addr}. Workspace standing by.",
]
_AFTERNOON = [
    "Good afternoon {addr}. Systems active.",
    "Afternoon {addr}. Still running smoothly.",
    "Good afternoon {addr}. What's next?",
    "Good afternoon {addr}. Kya plan hai?",
    "Afternoon {addr}. Ready for whatever you need.",
    "Good afternoon {addr}. All systems nominal.",
    "Good afternoon {addr}. Deep work time?",
    "Afternoon {addr}. Kaam pe lagte hain?",
]
_EVENING = [
    "Good evening {addr}. How did the day go?",
    "Evening {addr}. Systems online.",
    "Good evening {addr}. Aaj ka kya haal?",
    "Good evening {addr}. Still working?",
    "Evening {addr}. Main ready hoon.",
    "Good evening {addr}. Wrap up karna hai ya aur kaam?",
    "Evening {addr}. Systems are holding steady.",
]
_NIGHT = [
    "Working late again {addr}. Main hoon.",
    "It's late {addr}. Main yahin hoon.",
    "Still at it {addr}? Systems are with you.",
    "Late night session {addr}. Ready.",
    "Raat ko bhi kaam {addr}? Kaafi coffee pi li?",
    "Middle of the night {addr}. Chal karte hain.",
    "Late again {addr}. Main ready hoon.",
]
_RETURN = [
    "Welcome back {addr}. Everything was monitored.",
    "Welcome back {addr}. Systems ready.",
    "Good to have you back {addr}. All clear.",
    "Back already {addr}? Ready.",
    "Welcome back {addr}. Kuch naya?",
    "Aa gaye {addr}. Main ready hoon.",
    "Welcome back. Systems nominal {addr}.",
    "There you are {addr}. All good here.",
]

# ── First-boot intro (runs exactly once) ─────────────────────────────────────
_FIRST_BOOT = (
    "Good {period} Rajveer. All systems are online and operational. "
    "I am J.A.R.V.I.S. — your personal AI operating system. "
    "Whenever you are ready, just speak."
)

_FIRST_BOOT_FLAG    = "memory/first_boot_done.json"
_LAST_GREETING_FILE = "memory/last_greeting.json"


def _is_first_boot() -> bool:
    return not os.path.exists(_FIRST_BOOT_FLAG)


def _mark_boot_done() -> None:
    os.makedirs("memory", exist_ok=True)
    with open(_FIRST_BOOT_FLAG, "w") as f:
        json.dump({"done": True}, f)


def _load_last() -> Optional[str]:
    try:
        if os.path.exists(_LAST_GREETING_FILE):
            with open(_LAST_GREETING_FILE) as f:
                return json.load(f).get("last")
    except Exception:
        pass
    return None


def _save_last(greeting: str) -> None:
    try:
        os.makedirs("memory", exist_ok=True)
        with open(_LAST_GREETING_FILE, "w") as f:
            json.dump({"last": greeting}, f)
    except Exception:
        pass


def _pick_address(memory=None) -> str:
    addresses = ["Sir", "Boss", "Rajveer"]
    last = None
    if memory:
        try:
            last = memory.recall("last_address", None)
        except Exception:
            pass
    choices = [a for a in addresses if a != last]
    if not choices:
        choices = addresses
    addr = random.choice(choices)
    if memory:
        try:
            memory.remember("last_address", addr)
        except Exception:
            pass
    return addr


def _pick(pool: list, addr: str, last: Optional[str]) -> str:
    formatted = [g.format(addr=addr) for g in pool]
    choices   = [g for g in formatted if g != last]
    if not choices:
        choices = formatted
    return random.choice(choices)


# ── Public API ────────────────────────────────────────────────────────────────

def time_aware_greeting(memory=None, context: str = "startup") -> str:
    """
    Original signature preserved.
    context: "startup" (default) | "return"
    """
    now  = datetime.datetime.now()
    h    = now.hour
    last = _load_last()

    # First-ever boot — cinematic, never repeated
    if context == "startup" and _is_first_boot():
        _mark_boot_done()
        period   = "morning" if h < 12 else "afternoon" if h < 17 else "evening"
        greeting = _FIRST_BOOT.format(period=period)
        _save_last(greeting)
        return greeting

    addr = _pick_address(memory)

    if context == "return":
        greeting = _pick(_RETURN, addr, last)
        _save_last(greeting)
        return greeting

    if 5 <= h < 12:
        pool = _MORNING
    elif 12 <= h < 17:
        pool = _AFTERNOON
    elif 17 <= h < 22:
        pool = _EVENING
    else:
        pool = _NIGHT

    base = _pick(pool, addr, last)

    # Wisdom ~15% on morning startup
    if context == "startup" and h < 12 and random.random() < 0.15:
        base = f"{base}\n\n{random.choice(_WISDOM)}"

    _save_last(base)
    return base


def return_greeting(memory=None) -> str:
    """Called when user says 'I'm back' or wakes from standby."""
    return time_aware_greeting(memory=memory, context="return")
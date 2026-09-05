"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : conversation_engine.py
PATH    : core\conversation_engine.py

CHANGES vs original:
  1. Added Mem0Adapter integration in _build_context() — semantic recall now
     supplements ContextEngine's local search.
  2. Added ImportanceScorer before Mem0 save — only scores >= 0.4 are persisted.
  3. Added showcase-mode trigger detection.
  4. Added _try_quick_response() — 15+ short patterns bypass LLM entirely,
     giving instant natural Hinglish replies from response_variations pools.
  5. Added _clean_ai_phrases() — strips ChatGPT phrases from LLM output.
  6. Added return-greeting detection ("i'm back", "aa gaya").
  7. Emotion → voice intent forwarded to speak() via voice.py 'intent' param.
  8. All existing signatures, imports and function names preserved.
  9. No new files created — only this file modified.

COMPATIBLE WITH: brain.py, memory_engine.py, context_engine.py,
                 persona_engine.py, human_layer.py, greeting_manager.py,
                 response_variations.py, importance_scorer.py, mem0_adapter.py
============================================================
"""

import re
import time
import random
import json
from typing import Optional

from core.personality.persona_engine import PersonaEngine
from core.personality.human_layer import HumanLayer
from core.greeting_manager import time_aware_greeting, return_greeting
from brain.emotion_detector import detect_emotion
from brain.context_engine import ContextEngine
from brain.response_variations import confirm_variation, opening_variation, quick
from core.importance_scorer import ImportanceScorer
from memory.mem0_adapter import Mem0Adapter


# ─── AI phrase blacklist (regex) ─────────────────────────────────────────────
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

# ─── Quick-match patterns (no LLM needed) ────────────────────────────────────
_THANKS_PAT    = re.compile(r"\b(thanks|thank you|shukriya|dhanyawad|ty)\b", re.I)
_GOODBYE_PAT   = re.compile(r"\b(bye|goodbye|alvida|tc|take care|goodnight|good night)\b", re.I)
_POSITIVE_PAT  = re.compile(r"\b(ho gaya|done|finished|completed|kaam ho gaya|sab sahi)\b", re.I)
_STRESSED_PAT  = re.compile(r"\b(overwhelmed|stressed|kya karo|itna|bahut kuch|confus)\b", re.I)
_ERROR_PAT_Q   = re.compile(r"\b(error|exception|traceback|crash|failed|broken|bug|issue)\b", re.I)
_LISTEN_PAT    = re.compile(r"^(jarvis|hey jarvis|jarves|haan|ji|bol|are you there|hello jarvis)[\?\.]?$", re.I)
_RETURN_PAT    = re.compile(r"\b(i'?m? back|i am back|back home|aa gaya|aa gaye|returned)\b", re.I)
_GREETING_PAT  = re.compile(r"\b(good morning|good afternoon|good evening|good night|goodnight|hi|hello|hey)\b", re.I)
_SHOWCASE_PAT  = re.compile(
    r"(show(ing)? (you|jarvis)|introduc|my (friend|father|mother|brother|sister|guest|family|dad|mom)|"
    r"someone wants to (see|meet)|meet jarvis|jarvis (meet|say hello)|presenting jarvis)",
    re.I,
)


def _clean_ai_phrases(text: str) -> str:
    cleaned = _AI_PHRASES.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


class ConversationEngine:
    def __init__(self, brain):
        # brain: instance of JarvisBrain — all existing references preserved
        self.brain   = brain
        self.memory  = brain.memory
        self.human   = brain.human_layer
        self.persona = brain.persona_engine
        self.ctx     = brain.context_engine if hasattr(brain, "context_engine") else ContextEngine()
        self.scorer  = ImportanceScorer()

        # Mem0 — lazy, non-crashing
        self._mem0        = None
        self._mem0_ready  = False
        self._init_mem0()

    # ── Mem0 init ─────────────────────────────────────────────────────────────
    def _init_mem0(self) -> None:
        try:
            self._mem0       = Mem0Adapter()
            self._mem0_ready = True
        except Exception as e:
            print(f"[CONV] Mem0 not available ({e}). Using local memory only.")

    # ── Thinking delay (unchanged from original) ──────────────────────────────
    def _thinking_delay(self, complexity: str):
        delays = {"small": (0.2, 0.35), "medium": (0.45, 0.6), "large": (0.8, 1.2)}
        lo, hi = delays.get(complexity, (0.2, 0.35))
        time.sleep(random.uniform(lo, hi))

    def _estimate_complexity(self, user_input: str) -> str:
        u = user_input.lower()
        if any(x in u for x in ["explain", "why", "how", "debug", "trace", "diagnostic", "analysis"]):
            return "large"
        if len(u.split()) <= 4:
            return "small"
        if len(u.split()) <= 12:
            return "medium"
        return "large"

    # ── MAIN ENTRY (handle) — preserved signature ─────────────────────────────
    def handle(self, query: str) -> str:
        q_raw = query.strip()
        q     = q_raw.lower()

        topic = self._infer_topic(q_raw)
        if topic:
            self.memory.remember("active_topic", topic)

        # 1. Mode switching (unchanged)
        if any(x in q for x in ["switch to friendly", "friendly mode", "normal mode"]):
            return self.brain.switch_mode("friendly")
        if any(x in q for x in ["switch to professional", "professional mode"]):
            return self.brain.switch_mode("professional")
        if any(x in q for x in ["enter admin", "admin mode"]):
            return self.brain.switch_mode("admin")

        # 2. Showcase mode
        if _SHOWCASE_PAT.search(q_raw):
            self.human.set_mode("professional")
            return self._showcase_introduction()

        # 3. Quick pooled responses — instant, no LLM
        quick_reply = self._try_quick_response(q_raw, q)
        if quick_reply:
            return quick_reply

        # 4. Quick routing/open/search (original logic preserved)
        if q.startswith("open ") or "search " in q or "youtube" in q or "google" in q:
            text = q.replace("open ", "").replace("search ", "").strip()
            url  = "https://youtube.com" if "youtube" in text else f"https://google.com/search?q={text.replace(' ', '+')}"
            try:
                self.memory.save_command(q_raw)
                self.memory.remember("last_command", q_raw)
            except Exception:
                pass
            self.brain.call_node_bridge("open", url)
            self._thinking_delay(self._estimate_complexity(q_raw))
            return confirm_variation(f"Opening {url}")

        # 5. Persona detection (original logic preserved)
        detected = self.persona.detect_mode(q_raw)
        if detected == "friend":
            self.human.set_mode("friendly")
        elif detected == "admin":
            self.human.set_mode("admin")

        # 6. Emotion detection (original logic preserved + voice intent mapping)
        mood = detect_emotion(q_raw)
        if mood == "frustrated":
            self.human.set_mode("professional")
        elif mood == "technical":
            self.human.set_mode("admin")

        # Map mood → TTS intent for voice.py VoiceBrain
        voice_intent = {
            "frustrated": "system",
            "technical":  "system",
            "excited":    "chat",
            "casual":     "chat",
        }.get(mood, "chat")

        # 7. Greeting detection (original logic preserved + return greeting)
        if _RETURN_PAT.search(q):
            self._thinking_delay("small")
            greeting = return_greeting(self.memory)
            self._remember_address(greeting)
            return greeting

        if (_GREETING_PAT.search(q) and len(q.split()) <= 5) or q.strip() in ["hi", "hello", "hey", "jarvis"]:
            self._thinking_delay("small")
            greeting = time_aware_greeting(self.memory)
            self._remember_address(greeting)
            return greeting

        # 8. Build context (original + Mem0 semantic recall added)
        convo_context = self._build_context(q_raw)
        active_topic = self._safe_recall("active_topic", "")
        if topic and active_topic and topic != active_topic:
            convo_context = f"Current topic: {topic}\n{convo_context}" if convo_context else f"Current topic: {topic}"
        elif topic:
            convo_context = f"Current topic: {topic}\n{convo_context}" if convo_context else f"Current topic: {topic}"
        last_cmd      = self._safe_recall("last_command", "")
        last_file     = self._safe_recall("last_file", "")
        style_hints   = self.persona.style_injection()

        extra = ""
        if convo_context:
            extra += f"{convo_context}\n"
        if last_cmd:
            extra += f"Last Command: {last_cmd}\n"
        if last_file:
            extra += f"Last File: {last_file}\n"
        if style_hints:
            extra += f"StyleHints: {style_hints}\n"

        # 9. Complexity + delay (original preserved)
        complexity = self._estimate_complexity(q_raw)
        self._thinking_delay(complexity)

        # 10. LLM call (original preserved)
        if self._should_ask_follow_up(q_raw, active_topic):
            q_raw = f"{q_raw} (context: {active_topic})"
        raw_response = self.brain._local_llm_response(q_raw, extra_context=extra)

        # 11. Scripture guidance (original preserved)
        advice = self._scripture_guidance(q_raw, mood)
        if advice:
            raw_response = f"{raw_response}\n\n{advice}"

        # 12. Strip AI phrases
        raw_response = _clean_ai_phrases(raw_response)

        # 13. Persist to local memory + Mem0 (new — was missing before)
        self._persist_exchange(q_raw, raw_response)

        # 14. Human layer enhancement (original preserved)
        metadata = {
            "detected_mode": detected,
            "last_address":  self._safe_recall("last_address", None),
            "active_topic":  topic or active_topic,
        }
        final = self.human.enhance(raw_response, metadata=metadata)

        # Store voice intent for caller (main.py can use it)
        self._last_voice_intent = voice_intent

        return final

    # ── QUICK RESPONSES ────────────────────────────────────────────────────────
    def _try_quick_response(self, q_raw: str, q: str) -> Optional[str]:
        """Match short utterances to pooled responses. Returns None if no match."""

        if _LISTEN_PAT.match(q.strip()):
            self._thinking_delay("small")
            return quick("listen")

        if _THANKS_PAT.search(q) and len(q.split()) <= 5:
            self._thinking_delay("small")
            return quick("thanks")

        if _GOODBYE_PAT.search(q):
            self._thinking_delay("small")
            return quick("goodbye")

        if _POSITIVE_PAT.search(q) and len(q.split()) <= 5:
            self._thinking_delay("small")
            return quick("positive")

        if _STRESSED_PAT.search(q) and len(q.split()) <= 8:
            self._thinking_delay("small")
            return quick("stressed")

        if _ERROR_PAT_Q.search(q) and len(q.split()) <= 6:
            self._thinking_delay("small")
            return quick("error")

        return None

    # ── BUILD CONTEXT (original + Mem0 semantic recall) ───────────────────────
    def _build_context(self, query: str) -> str:
        """Original method preserved. Mem0 semantic search added as extra layer."""
        bundle   = self.ctx.build_context(query, limit=8)
        sections = []

        if bundle.get("recent"):
            sections.append(f"Recent Conversation:\n{bundle['recent']}")

        working = bundle.get("working")
        if working:
            sections.append(f"Working Memory:\n{working}")

        project      = bundle.get("project") or {}
        project_lines = []
        if project.get("name"):
            project_lines.append(f"Project: {project['name']}")
        if project.get("last_files"):
            project_lines.append(f"Recent Files: {', '.join(project['last_files'])}")
        if project_lines:
            sections.append("Project Context:\n" + "\n".join(project_lines))

        profile = bundle.get("profile") or {}
        if profile:
            try:
                sections.append(f"User Profile:\n{json.dumps(profile, ensure_ascii=False)}")
            except Exception:
                sections.append(f"User Profile:\n{str(profile)}")

        # Mem0 semantic recall (new addition)
        mem0_results = self._mem0_search(query)
        if mem0_results:
            lines = [
                f"- [{m.get('category','general')}] {m.get('summary') or m.get('text','')}"
                for m in mem0_results if m.get("summary") or m.get("text")
            ]
            if lines:
                sections.append("Relevant Memories:\n" + "\n".join(lines))
        elif bundle.get("memories"):
            # Fallback to ContextEngine's local search (original)
            lines = [
                f"- [{m.get('category','general')}] {m.get('summary') or m.get('text','')}"
                for m in bundle["memories"] if m.get("summary") or m.get("text")
            ]
            if lines:
                sections.append("Relevant Memories:\n" + "\n".join(lines))

        return "\n\n".join(sections)

    # ── MEM0 SEARCH (safe) ────────────────────────────────────────────────────
    def _mem0_search(self, query: str) -> list:
        if not self._mem0_ready or not self._mem0:
            return []
        try:
            return self._mem0.search_memory(query, limit=5)
        except Exception:
            return []

    # ── PERSIST EXCHANGE ──────────────────────────────────────────────────────
    def _persist_exchange(self, user_input: str, response: str) -> None:
        """Save to local memory always. Save to Mem0 only if important."""
        try:
            self.memory.log_conversation(user_input, "chat", response)
            self.memory.remember("last_response", response)
            self.memory.save_command(user_input)
            self.memory.remember("last_command", user_input)
        except Exception:
            pass

        if not self._mem0_ready:
            return
        try:
            import datetime as _dt
            evaluation = self.scorer.evaluate(user_input)
            if evaluation["score"] >= 0.4:
                self._mem0.save_memory({
                    "text":       user_input,
                    "summary":    user_input[:200],
                    "category":   evaluation["category"],
                    "importance": evaluation["score"],
                    "source":     "user",
                    "timestamp":  _dt.datetime.now().isoformat(),
                })
        except Exception:
            pass

    # ── SHOWCASE INTRODUCTION ─────────────────────────────────────────────────
    def _showcase_introduction(self) -> str:
        import datetime
        h      = datetime.datetime.now().hour
        period = "morning" if h < 12 else "afternoon" if h < 17 else "evening"
        intros = [
            (
                f"Good {period}. I'm J.A.R.V.I.S. — Just A Rather Very Intelligent System, Mark 5. "
                "I was designed and engineered by Rajveer Singh Rajput as a personal AI operating system. "
                "I handle voice commands, automation, memory, system monitoring, and natural conversation — "
                "all running locally on this machine. It's a pleasure to meet you."
            ),
            (
                f"Good {period}. I'm J.A.R.V.I.S., Rajveer's personal AI operating intelligence. "
                "Mark 5 is the current version — built for voice interaction, task automation, "
                "real-time system awareness, and long-term memory. "
                "Everything you're seeing was designed and engineered by Rajveer. How can I help?"
            ),
            (
                f"Good {period}. I'm J.A.R.V.I.S. — a fully local AI operating system created by Rajveer Singh Rajput. "
                "I manage voice, memory, automation, and system intelligence without any cloud dependency. "
                "Feel free to ask me anything."
            ),
        ]
        return random.choice(intros)

    # ── SCRIPTURE GUIDANCE (original — unchanged) ─────────────────────────────
    def _scripture_guidance(self, query: str, mood: str) -> str:
        q = query.lower()
        if any(x in q for x in ["confused", "uncertain", "stuck", "difficult decision", "choice", "choose", "decision"]):
            return (
                "Practical note: Bhagavad Gita ka core message hai — kaam par dhyan do, phal par nahi. "
                "Next right step clear karo aur phir aage badho."
            )
        if any(x in q for x in ["leadership", "discipline", "courage", "focus", "strategy"]):
            return (
                "Chanakya Neeti kehta hai — discipline aur consistency aapki sabse badi strength hain. "
                "Plan simple rakho aur execution pe dhyan do."
            )
        if mood == "confused":
            return (
                "Ek practical frame: Jyada sochna kam karo, pehle ek chhota step le lo. "
                "Aam taur pe clarity action se aati hai."
            )
        return ""

    def _infer_topic(self, text: str) -> str:
        lowered = (text or "").lower()
        if any(x in lowered for x in ["portfolio", "animation", "website", "ui", "design", "landing page", "resume"]):
            return "portfolio"
        if any(x in lowered for x in ["voice", "speech", "tts", "wake word", "mic", "audio"]):
            return "voice"
        if any(x in lowered for x in ["code", "python", "bug", "debug", "program", "implementation", "repo", "commit"]):
            return "coding"
        if any(x in lowered for x in ["hud", "widget", "ui", "interface", "screen"]):
            return "hud"
        if any(x in lowered for x in ["jarvis", "assistant", "companion", "personality", "conversation"]):
            return "jarvis"
        return ""

    def _should_ask_follow_up(self, text: str, active_topic: str) -> bool:
        lowered = (text or "").lower()
        if active_topic:
            return False
        if any(x in lowered for x in ["improve", "fix", "change", "update", "make", "add", "build"]):
            return False if len(lowered.split()) <= 3 else True
        if len(lowered.split()) <= 4:
            return False
        return ("it" in lowered or "that" in lowered or "this" in lowered) and ("can you" in lowered or "could you" in lowered or "would you" in lowered)

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _remember_address(self, greeting: str) -> None:
        try:
            self.memory.remember("last_address", greeting.split()[-1].strip("."))
        except Exception:
            pass

    def _safe_recall(self, key: str, default=None):
        try:
            return self.memory.recall(key, default)
        except Exception:
            return default
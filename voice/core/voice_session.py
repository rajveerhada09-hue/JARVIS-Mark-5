"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : voice_session.py
PATH    : voice/voice_session.py

PURPOSE :
Defines VoiceSession — the single data structure representing one
spoken utterance as it moves through TTS generation, playback, possible
interruption, and possible resume. Every other voice/ module
(voice.py, audio_controller.py, resume_manager.py, barge_listener.py,
voice_manager.py) operates on VoiceSession instances rather than raw
strings, so state (sentence position, emotion, playback status) travels
with the utterance instead of being tracked independently in several
places — this is the single source of truth the "no duplicated logic"
requirement depends on.

Also defines:
    Emotion         — fixed emotion vocabulary used for TTS styling.
    PlaybackState   — fixed state machine for a session's lifecycle.
    split_sentences — the ONE sentence-splitting implementation every
                      other voice/ module imports rather than
                      reimplementing.

LAST UPDATED : 2026-07-10
============================================================
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

__all__ = ["VoiceSession", "Emotion", "PlaybackState", "split_sentences"]


class Emotion(str, Enum):
    """
    Fixed emotion vocabulary used to select ElevenLabs voice_settings
    and, for the Edge-TTS fallback, the closest available prosody
    approximation. Kept as a str-mixin Enum (not enum.StrEnum, which is
    3.11+ only and unnecessary here) so values compare directly against
    plain strings without extra conversion.
    """

    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    SERIOUS = "serious"
    CONFIDENT = "confident"
    FIRM = "firm"
    LIGHT = "light"


class PlaybackState(str, Enum):
    """Lifecycle states for a VoiceSession's audio playback."""

    IDLE = "idle"
    QUEUED = "queued"
    SPEAKING = "speaking"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def split_sentences(text: str) -> List[str]:
    """
    Split `text` into speakable sentence units.

    This is the single, canonical sentence-splitting implementation for
    the entire voice/ package. voice.py uses it to synthesize
    sentence-by-sentence; resume_manager.py relies on the resulting list
    being identical to the one stored on the VoiceSession it resumes, so
    no other module should reimplement this logic — import it from here.

    Deliberately simple and fast rather than a full NLP tokenizer, which
    is the right tradeoff for short conversational TTS output rather
    than long-form documents.

    Args:
        text: Raw text to split.

    Returns:
        A list of non-empty, stripped sentence strings. Empty list if
        `text` is empty or whitespace-only.
    """
    if not text:
        return []
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = _SENTENCE_BOUNDARY.split(cleaned)
    return [p.strip() for p in parts if p.strip()]


@dataclass
class VoiceSession:
    """
    A single spoken utterance, tracked end-to-end from creation through
    playback, interruption, and possible resume.

    Attributes:
        text:            The full, original text to be spoken.
        intent:          Free-form intent label (e.g. "chat",
                         "pc_control", "system") — matches the loose
                         string convention already used elsewhere in
                         JARVIS's conversation/voice pipeline.
        emotion:         The Emotion this session should be spoken with.
        is_resumable:    Whether this session is eligible for resume if
                         interrupted. Very short, low-priority
                         utterances (e.g. "Yes?") may be created with
                         this False, since resuming a single-word
                         utterance has no practical meaning.
        session_id:      Unique identifier for this session (UUID4 hex
                         string). Used as the resume-registry key.
        created_at:      Local timestamp of session creation.
        sentence_list:   `text` pre-split into sentences via
                         split_sentences(). Populated automatically in
                         __post_init__ if not supplied explicitly, so
                         every module consuming this session agrees on
                         sentence boundaries.
        sentence_index:  Index into sentence_list of the NEXT sentence
                         to be spoken. Advances as playback progresses;
                         on interruption this is exactly where resume
                         picks back up.
        audio_path:      Filesystem path of the currently-loaded audio
                         clip for the CURRENT sentence. Sessions are
                         synthesized and played sentence-by-sentence
                         (not one file for the whole utterance) so
                         barge-in latency stays low — playback can start
                         after the first sentence is ready rather than
                         waiting for the entire response to synthesize.
        playback_state:  Current PlaybackState.
    """

    text: str
    intent: str = "chat"
    emotion: Emotion = Emotion.NEUTRAL
    is_resumable: bool = True

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=datetime.now)
    sentence_list: List[str] = field(default_factory=list)
    sentence_index: int = 0
    audio_path: Optional[str] = None
    playback_state: PlaybackState = PlaybackState.IDLE

    def __post_init__(self) -> None:
        if not self.sentence_list:
            self.sentence_list = split_sentences(self.text)

    @classmethod
    def create(
        cls,
        text: str,
        intent: str = "chat",
        emotion: Emotion = Emotion.NEUTRAL,
        is_resumable: bool = True,
    ) -> "VoiceSession":
        """Preferred factory constructor over calling VoiceSession(...) directly."""
        return cls(text=text, intent=intent, emotion=emotion, is_resumable=is_resumable)

    @property
    def total_sentences(self) -> int:
        """Total number of sentences in this session."""
        return len(self.sentence_list)

    @property
    def is_complete(self) -> bool:
        """True once every sentence has been spoken (index advanced past the end)."""
        return self.sentence_index >= self.total_sentences

    @property
    def remaining_sentences(self) -> List[str]:
        """Sentences from the current index onward — exactly what resume needs to replay."""
        if self.sentence_index >= self.total_sentences:
            return []
        return self.sentence_list[self.sentence_index:]

    @property
    def remaining_text(self) -> str:
        """The remaining sentences rejoined into a single string."""
        return " ".join(self.remaining_sentences)

    def current_sentence(self) -> Optional[str]:
        """The sentence at the current index, or None if playback is complete."""
        if 0 <= self.sentence_index < self.total_sentences:
            return self.sentence_list[self.sentence_index]
        return None

    def advance(self) -> None:
        """
        Move to the next sentence. Marks the session COMPLETED if that
        was the last sentence. Called by AudioController/VoiceManager
        after each sentence finishes playing without interruption.
        """
        self.sentence_index += 1
        if self.is_complete:
            self.playback_state = PlaybackState.COMPLETED

    def mark_interrupted(self) -> None:
        """
        Record that playback stopped mid-utterance. sentence_index is
        left exactly where it was, so resume_manager.py can resume from
        this precise point.
        """
        self.playback_state = PlaybackState.INTERRUPTED

    def mark_speaking(self) -> None:
        self.playback_state = PlaybackState.SPEAKING

    def mark_paused(self) -> None:
        self.playback_state = PlaybackState.PAUSED

    def mark_queued(self) -> None:
        self.playback_state = PlaybackState.QUEUED

    def mark_failed(self) -> None:
        self.playback_state = PlaybackState.FAILED

    def reset_for_resume(self) -> None:
        """
        Prepare this session to resume playback from its current
        sentence_index. Only takes effect if the session is actually in
        the INTERRUPTED state — calling this on a session in any other
        state is a no-op, since only an interrupted session has a
        meaningful resume point.
        """
        if self.playback_state == PlaybackState.INTERRUPTED:
            self.playback_state = PlaybackState.QUEUED

    def to_dict(self) -> dict:
        """
        Plain-dict snapshot for logging, HUD status reporting, or
        handing to resume_manager.py's persistence layer. All values are
        JSON-serializable (Enum members and datetime are converted to
        strings).
        """
        return {
            "session_id": self.session_id,
            "text": self.text,
            "intent": self.intent,
            "emotion": self.emotion.value,
            "is_resumable": self.is_resumable,
            "created_at": self.created_at.isoformat(),
            "sentence_list": list(self.sentence_list),
            "sentence_index": self.sentence_index,
            "total_sentences": self.total_sentences,
            "audio_path": self.audio_path,
            "playback_state": self.playback_state.value,
        }

    def __repr__(self) -> str:
        return (
            f"<VoiceSession id={self.session_id[:8]} "
            f"state={self.playback_state.value} "
            f"sentence={self.sentence_index}/{self.total_sentences} "
            f"emotion={self.emotion.value} intent={self.intent!r}>"
        )
"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : resume_manager.py
PATH    : voice/resume_manager.py

PURPOSE :
Stores interrupted VoiceSession objects and provides a
single global resume point.

This module NEVER performs playback.

It ONLY stores/retrieves VoiceSession objects.

Every interruption replaces the previous resume session.

============================================================
"""

from __future__ import annotations

import threading
from typing import Optional

from voice.voice_session import (
    VoiceSession,
    PlaybackState,
)


class ResumeManager:
    """
    Singleton-style resume manager.

    Only one interrupted session exists at a time.

    Responsibilities:

        • store interrupted session
        • retrieve session
        • clear session
        • check if resume exists
    """

    def __init__(self):

        self._lock = threading.Lock()

        self._session: Optional[VoiceSession] = None

    # -------------------------------------------------

    def save(self, session: VoiceSession) -> None:
        """
        Save an interrupted session.

        Previous resume session is overwritten.
        """

        if session is None:
            return

        if not session.is_resumable:
            return

        session.mark_interrupted()

        with self._lock:
            self._session = session

    # -------------------------------------------------

    def get(self) -> Optional[VoiceSession]:
        """
        Return current interrupted session.

        Does NOT remove it.
        """

        with self._lock:
            return self._session

    # -------------------------------------------------

    def pop(self) -> Optional[VoiceSession]:
        """
        Return current session and clear manager.
        """

        with self._lock:

            session = self._session

            self._session = None

            if session:

                session.reset_for_resume()

            return session

    # -------------------------------------------------

    def clear(self) -> None:

        with self._lock:
            self._session = None

    # -------------------------------------------------

    def has_pending(self) -> bool:

        with self._lock:

            return self._session is not None

    # -------------------------------------------------

    def status(self) -> dict:
        """
        Debug information.
        """

        with self._lock:

            if self._session is None:

                return {
                    "pending": False
                }

            return {
                "pending": True,
                "session_id": self._session.session_id,
                "sentence_index": self._session.sentence_index,
                "total_sentences": self._session.total_sentences,
                "state": self._session.playback_state.value,
            }


# ==========================================================
# Global Singleton
# ==========================================================

resume_manager = ResumeManager()
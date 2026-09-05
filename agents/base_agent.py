"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : base_agent.py
PATH    : agents/base_agent.py

PURPOSE :
Production-ready abstract base class for every JARVIS agent. Every
current and future agent (Research, Coding, Browser, Reviewer, Memory,
Security, ... — designed to scale to 30+) inherits from this.

ARCHITECTURAL DECISIONS (explained inline at each point below):
  1. Two of the six required methods (execute, can_handle) use a
     "concrete wrapper + protected abstract hook" pattern:
         execute()      -> calls self._execute()      (subclass implements)
         can_handle()    -> calls self._can_handle()   (subclass implements)
     These are the two methods called REPEATEDLY and at high frequency
     by whatever dispatches tasks, so centralizing busy-flag handling,
     timing, stats, health tracking, and exception safety in the base
     class means every agent gets this for free and correctly, instead
     of 30 separate implementations each needing to remember to do it.
  2. The other four (initialize, shutdown, status, on_event) are
     called rarely (once at startup/shutdown, occasionally for events,
     on-demand for status) — for these, subclasses get direct,
     un-wrapped override control, since the cost of an extra hook layer
     isn't justified by the call frequency, and a subclass may
     legitimately need full control over multi-step setup/teardown.
  3. Deliberately synchronous (no asyncio). Every other file in this
     project (voice.py, brain.py, conversation_engine.py) is
     synchronous/thread-based, not asyncio-based. Introducing async
     here would very likely be incompatible with however
     agent_manager.py currently calls agents. A subclass that needs
     concurrency can still spin up a thread inside its own _execute(),
     exactly like voice.py already does elsewhere in this project.
  4. AgentResult / AgentStats / AgentHealth are defined in THIS file
     rather than a separate shared "protocols" module, since this task
     scoped me to exactly one new file. If the project later adopts a
     shared types module, these can be extracted without changing this
     class's public surface.
  5. Kept dependency-free — stdlib only (abc, dataclasses, datetime,
     enum, logging, time, typing). No assumption that any other
     not-yet-built infrastructure (event bus, task contracts, etc.)
     exists yet.

LAST UPDATED : 2026-07-03
============================================================
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

__all__ = ["BaseAgent", "AgentResult", "AgentStats", "AgentHealth"]


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH STATUS
# str-based Enum so it's directly JSON/dict-serializable for a future HUD
# "live agent status" panel without any extra conversion step.
# ═══════════════════════════════════════════════════════════════════════════
class AgentHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION RESULT
# Every execute() call returns one of these — a consistent, structured
# contract regardless of which of 30+ agents ran, so whatever dispatches
# agents never needs agent-specific result handling.
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class AgentResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    skipped: bool = False
    skip_reason: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION STATISTICS
# Accumulated automatically by execute()'s wrapper — no subclass needs to
# update this itself. average/success_rate are computed on read rather
# than stored, so there is only ever one source of truth.
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class AgentStats:
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_execution_time: float = 0.0
    consecutive_failures: int = 0
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def average_execution_time(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.total_execution_time / self.total_runs

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 1.0  # no data yet — optimistic default, not a false 0%
        return self.successful_runs / self.total_runs


# ═══════════════════════════════════════════════════════════════════════════
# BASE AGENT
# ═══════════════════════════════════════════════════════════════════════════
class BaseAgent(ABC):
    """
    Abstract base class every JARVIS agent inherits from.

    Subclasses MUST implement:
        _execute(task)     -> Any            (the agent's actual work)
        _can_handle(task)  -> bool           (capability check)

    Subclasses MAY override (sensible defaults provided):
        initialize()  -> bool
        shutdown()    -> None
        on_event(event_type, payload)

    Subclasses should NOT override (base class owns this bookkeeping):
        execute()      — wraps _execute() with timing/stats/health/safety
        can_handle()    — wraps _can_handle() with the enabled-flag check
        status()        — reports the base class's own tracked state
    """

    # Consecutive-failure thresholds for automatic health degradation.
    # Class-level so a subclass can tune sensitivity by overriding these,
    # without needing to touch the health-tracking logic itself.
    DEGRADED_AFTER_FAILURES: int = 1
    UNHEALTHY_AFTER_FAILURES: int = 3

    def __init__(
        self,
        name: str,
        description: str = "",
        priority: int = 1,
        enabled: bool = True,
        capabilities: Optional[List[str]] = None,
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.priority: int = priority
        self.enabled: bool = enabled
        self.capabilities: List[str] = capabilities or []

        self.busy: bool = False
        self.health: AgentHealth = AgentHealth.UNKNOWN
        self.stats: AgentStats = AgentStats()

        self._initialized: bool = False

        # Logger helper: a properly-namespaced CHILD logger
        # ("jarvis.agent.<name>"), NOT a fresh logging.basicConfig() call.
        # brain.py already calls logging.basicConfig() once at import
        # time; calling it again here would be a no-op at best (Python
        # only honors the first basicConfig() call) and a silent
        # misconfiguration risk at worst. getLogger() correctly inherits
        # whatever root configuration is already in place.
        self._logger: logging.Logger = logging.getLogger(f"jarvis.agent.{name}")

    # ─────────────────────────────────────────────────────────────────
    # LOGGER HELPER
    # ─────────────────────────────────────────────────────────────────
    def log(self, message: str, level: str = "info") -> None:
        """Consistent, agent-prefixed logging. level: debug|info|warning|error|critical."""
        prefixed = f"[{self.name}] {message}"
        getattr(self._logger, level, self._logger.info)(prefixed)

    # ─────────────────────────────────────────────────────────────────
    # LIFECYCLE — initialize / shutdown
    # Directly overridable (see architectural decision #2 above). Base
    # implementations are safe no-ops that mark state correctly, so an
    # agent with no real setup/teardown needs to write zero extra code.
    # ─────────────────────────────────────────────────────────────────
    def initialize(self) -> bool:
        """
        One-time setup, called once by whatever manages agent lifecycle
        (e.g. AgentManager) before this agent is ever dispatched a task.
        Override for real setup (loading a model, opening a connection,
        etc.) — if overriding, either call super().initialize() first or
        set self._initialized = True and self.health = AgentHealth.HEALTHY
        yourself so status() reports correctly.
        """
        self._initialized = True
        self.health = AgentHealth.HEALTHY
        self.log("Initialized.")
        return True

    def shutdown(self) -> None:
        """
        Graceful teardown, called once when JARVIS is shutting down or
        this agent is being retired. Override for real teardown (closing
        connections, flushing buffers). Base implementation defensively
        clears the busy flag so a shutdown mid-execution never leaves
        the agent permanently reporting busy=True.
        """
        self.busy = False
        self._initialized = False
        self.log("Shut down.")

    # ─────────────────────────────────────────────────────────────────
    # EXECUTION — public wrapper (concrete) + protected hook (abstract)
    # ─────────────────────────────────────────────────────────────────
    def execute(self, task: Any) -> AgentResult:
        """
        Public entry point. Handles the disabled/busy guard, timing,
        stats, health tracking, and exception safety automatically —
        subclasses implement _execute() with pure business logic only
        and never need to touch any of this.
        """
        if not self.enabled:
            self.log("Execution skipped — agent is disabled.", level="warning")
            return AgentResult(success=False, skipped=True, skip_reason="agent_disabled")

        if self.busy:
            self.log("Execution skipped — agent is already busy.", level="warning")
            return AgentResult(success=False, skipped=True, skip_reason="agent_busy")

        self.busy = True
        start = time.monotonic()
        try:
            output = self._execute(task)
            duration = time.monotonic() - start
            self._record_success(duration)
            return AgentResult(success=True, output=output, duration_seconds=duration)
        except Exception as exc:
            duration = time.monotonic() - start
            self._record_failure(duration, str(exc))
            self.log(f"Execution failed after {duration:.2f}s: {exc}", level="error")
            return AgentResult(success=False, error=str(exc), duration_seconds=duration)
        finally:
            self.busy = False

    @abstractmethod
    def _execute(self, task: Any) -> Any:
        """
        Subclass implements the agent's actual work here. Raise on
        failure — execute() catches it and turns it into a structured
        AgentResult(success=False, ...); no need for the subclass to
        catch its own exceptions just to report failure.
        """
        raise NotImplementedError

    # ─────────────────────────────────────────────────────────────────
    # CAPABILITY CHECK — public wrapper (concrete) + protected hook (abstract)
    # ─────────────────────────────────────────────────────────────────
    def can_handle(self, task: Any) -> bool:
        """
        Public entry point for capability routing. A disabled agent
        always returns False here regardless of its own matching logic
        — this guarantees a disabled agent can never be selected, without
        relying on every subclass remembering to check self.enabled itself.
        """
        if not self.enabled:
            return False
        try:
            return self._can_handle(task)
        except Exception as exc:
            self.log(f"can_handle() check raised an exception: {exc}", level="error")
            return False

    @abstractmethod
    def _can_handle(self, task: Any) -> bool:
        """
        Subclass implements capability matching here. self.capabilities
        (a plain list set at construction) is available as optional
        metadata to check against — e.g. `return task.get("type") in
        self.capabilities` — but this hook has full freedom to implement
        any matching logic, not just a list-membership check.
        """
        raise NotImplementedError

    # ─────────────────────────────────────────────────────────────────
    # EVENTS — directly overridable, safe no-op default
    # ─────────────────────────────────────────────────────────────────
    def on_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Hook for a future event-bus system to call. Default is a no-op
        (most agents don't care about most events) — override to react
        to specific event_type values. Kept dependency-free: takes a
        plain string + dict rather than assuming a not-yet-built
        AgentMessage/event-bus type exists.
        """
        self.log(f"Unhandled event: {event_type}", level="debug")

    # ─────────────────────────────────────────────────────────────────
    # STATUS — concrete, JSON-friendly snapshot for HUD/orchestrator use
    # ─────────────────────────────────────────────────────────────────
    def status(self) -> Dict[str, Any]:
        """Return a plain-dict snapshot of this agent's current state and stats."""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "busy": self.busy,
            "initialized": self._initialized,
            "health": self.health.value,
            "capabilities": list(self.capabilities),
            "stats": {
                "total_runs": self.stats.total_runs,
                "successful_runs": self.stats.successful_runs,
                "failed_runs": self.stats.failed_runs,
                "success_rate": round(self.stats.success_rate, 3),
                "average_execution_time_s": round(self.stats.average_execution_time, 4),
                "consecutive_failures": self.stats.consecutive_failures,
                "last_run_at": self.stats.last_run_at.isoformat() if self.stats.last_run_at else None,
                "last_error": self.stats.last_error,
            },
        }

    @property
    def is_healthy(self) -> bool:
        return self.health == AgentHealth.HEALTHY

    # ─────────────────────────────────────────────────────────────────
    # INTERNAL — stats/health bookkeeping used only by execute()
    # ─────────────────────────────────────────────────────────────────
    def _record_success(self, duration: float) -> None:
        self.stats.total_runs += 1
        self.stats.successful_runs += 1
        self.stats.total_execution_time += duration
        self.stats.consecutive_failures = 0
        self.stats.last_run_at = datetime.now()
        self.stats.last_success_at = self.stats.last_run_at
        self.health = AgentHealth.HEALTHY

    def _record_failure(self, duration: float, error: str) -> None:
        self.stats.total_runs += 1
        self.stats.failed_runs += 1
        self.stats.total_execution_time += duration
        self.stats.consecutive_failures += 1
        self.stats.last_run_at = datetime.now()
        self.stats.last_failure_at = self.stats.last_run_at
        self.stats.last_error = error

        if self.stats.consecutive_failures >= self.UNHEALTHY_AFTER_FAILURES:
            self.health = AgentHealth.UNHEALTHY
        elif self.stats.consecutive_failures >= self.DEGRADED_AFTER_FAILURES:
            self.health = AgentHealth.DEGRADED

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} name={self.name!r} "
            f"priority={self.priority} enabled={self.enabled} "
            f"busy={self.busy} health={self.health.value}>"
        )
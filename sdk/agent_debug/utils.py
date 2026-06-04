"""Utility functions for AgentDebug SDK."""

import uuid
import time
from datetime import datetime, timezone


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return str(uuid.uuid4())


def current_iso_timestamp() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class Timer:
    """Simple stopwatch timer for measuring durations."""

    def __init__(self):
        self._start: float = 0.0
        self._elapsed: float = 0.0
        self._running: bool = False

    def start(self) -> None:
        """Start or restart the timer."""
        self._start = time.monotonic()
        self._running = True

    def stop(self) -> None:
        """Stop the timer and freeze elapsed time."""
        if self._running:
            self._elapsed = time.monotonic() - self._start
            self._running = False

    def elapsed_ms(self) -> int:
        """Return elapsed time in milliseconds."""
        if self._running:
            return int((time.monotonic() - self._start) * 1000)
        return int(self._elapsed * 1000)

    def reset(self) -> None:
        """Reset the timer."""
        self._start = 0.0
        self._elapsed = 0.0
        self._running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (~4 chars per token)."""
    return len(text) // 4


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text with ellipsis for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."

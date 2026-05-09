"""Provider-agnostic browser interface.

Worker only sees BrowserSession; never touches Kernel SDK directly. Lets us
swap Kernel ↔ Browserbase ↔ local-Chromium without touching worker code.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class BrowserSession(Protocol):
    """A live remote browser. Holds CDP + recording state."""

    @property
    def session_id(self) -> str: ...

    @property
    def cdp_ws_url(self) -> str: ...

    @property
    def live_view_url(self) -> str | None:
        """If the provider exposes a viewer URL (iframe-able), return it. Else None."""
        ...

    async def start_recording(self) -> str:
        """Begin capturing the session. Returns a recording_id."""
        ...

    async def stop_recording(self, recording_id: str) -> None: ...

    async def download_recording(self, recording_id: str, dest: Path) -> None:
        """Download the recording (typically mp4) to `dest`."""
        ...

    async def release(self) -> None:
        """Tear down the session. MUST be idempotent — workers call from finally."""
        ...


class BrowserProvider(Protocol):
    """Factory for BrowserSessions."""

    async def acquire(
        self,
        *,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        stealth: bool = True,
    ) -> BrowserSession: ...

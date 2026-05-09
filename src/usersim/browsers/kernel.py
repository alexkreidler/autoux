"""KernelProvider / KernelSession implementing the BrowserProvider/BrowserSession protocols."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from kernel import Kernel
from kernel.types import BrowserCreateResponse


class KernelSession:
    def __init__(self, handle: BrowserCreateResponse, kernel: Kernel) -> None:
        self._handle = handle
        self._kernel = kernel
        self._released = False

    @property
    def session_id(self) -> str:
        return self._handle.session_id

    @property
    def cdp_ws_url(self) -> str:
        return self._handle.cdp_ws_url

    @property
    def live_view_url(self) -> str | None:
        return self._handle.browser_live_view_url

    async def start_recording(self) -> str:
        resp = await asyncio.to_thread(
            self._kernel.browsers.replays.start, self._handle.session_id
        )
        return resp.replay_id

    async def stop_recording(self, recording_id: str) -> None:
        await asyncio.to_thread(
            self._kernel.browsers.replays.stop,
            recording_id,
            id=self._handle.session_id,
        )

    async def download_recording(self, recording_id: str, dest: Path) -> None:
        def _dl():
            resp = self._kernel.browsers.replays.download(
                recording_id, id=self._handle.session_id
            )
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())

        await asyncio.to_thread(_dl)

    async def release(self) -> None:
        if self._released:
            return
        self._released = True
        try:
            await asyncio.to_thread(
                self._kernel.browsers.delete_by_id, self._handle.session_id
            )
        except Exception as e:
            import sys
            print(f"[kernel] release failed for {self._handle.session_id}: {e}", file=sys.stderr)


class KernelProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self._kernel = Kernel(api_key=api_key or os.environ["KERNEL_API_KEY"])

    async def acquire(
        self,
        *,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        stealth: bool = True,
    ) -> KernelSession:
        handle = await asyncio.to_thread(
            self._kernel.browsers.create,
            stealth=stealth,
            viewport={"width": viewport_width, "height": viewport_height},
        )
        return KernelSession(handle, self._kernel)

from __future__ import annotations

from typing import Protocol


class InstrumentAnalyzer(Protocol):
    def analyze(
        self,
        genre: str,
        bars: list[dict],
        beats: list[dict],
        stems_dir: str | None,
        tempo: float,
    ) -> dict: ...

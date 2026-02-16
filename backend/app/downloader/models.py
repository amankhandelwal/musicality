from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DownloadResult:
    audio_path: str
    title: str
    duration: float

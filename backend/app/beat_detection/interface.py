from __future__ import annotations

from typing import Protocol

from app.beat_detection.models import BeatDetectionResult


class BeatDetector(Protocol):
    def detect(self, audio_path: str) -> BeatDetectionResult: ...

from __future__ import annotations

from typing import Protocol

from app.separator.models import SeparationResult


class SourceSeparator(Protocol):
    def separate(self, audio_path: str, output_dir: str | None = None) -> SeparationResult: ...

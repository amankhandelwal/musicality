from __future__ import annotations

from typing import Protocol

from app.genre.models import InstrumentTemplate


class GenreTemplateProvider(Protocol):
    def get_templates(self, genre: str) -> list[InstrumentTemplate]: ...

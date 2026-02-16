from __future__ import annotations

from pydantic import BaseModel

from app.genre.models import GenreHint


class Beat(BaseModel):
    time: float
    beat_num: int


class Bar(BaseModel):
    start: float
    end: float
    bar_num: int


class BeatCell(BaseModel):
    active: bool
    velocity: float = 0.0
    pitch: float = 0.5


class InstrumentBeat(BaseModel):
    instrument: str
    beats: list[bool] | list[BeatCell]
    confidence: float


class BarInstruments(BaseModel):
    bar_num: int
    instruments: list[InstrumentBeat]


class InstrumentGrid(BaseModel):
    genre: str
    instrument_list: list[str]
    subdivisions: int = 16
    bars: list[BarInstruments]


class Metadata(BaseModel):
    title: str
    duration: float
    genre_hint: GenreHint


class AnalysisResult(BaseModel):
    metadata: Metadata
    tempo: float
    beats: list[Beat]
    bars: list[Bar]
    instrument_grid: InstrumentGrid

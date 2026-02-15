from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class GenreHint(str, Enum):
    SALSA = "salsa"
    BACHATA = "bachata"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DETECTING_BEATS = "detecting_beats"
    SEPARATING_STEMS = "separating_stems"
    DETECTING_SECTIONS = "detecting_sections"
    ANALYZING_INSTRUMENTS = "analyzing_instruments"
    MAPPING_SECTIONS = "mapping_sections"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    url: str


class Beat(BaseModel):
    time: float
    beat_num: int


class Bar(BaseModel):
    start: float
    end: float
    bar_num: int


class Section(BaseModel):
    start: float
    end: float
    label: str
    latin_label: str


class InstrumentBeat(BaseModel):
    instrument: str
    beats: list[bool]
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
    sections: list[Section]
    instrument_grid: InstrumentGrid


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    error: str | None = None
    result: AnalysisResult | None = None

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BeatCell:
    active: bool
    velocity: float = 0.0
    pitch: float = 0.5


@dataclass
class InstrumentBeat:
    instrument: str
    beats: list[dict]
    confidence: float


@dataclass
class BarInstruments:
    bar_num: int
    instruments: list[InstrumentBeat]


@dataclass
class InstrumentGrid:
    genre: str
    instrument_list: list[str]
    subdivisions: int
    bars: list[BarInstruments]

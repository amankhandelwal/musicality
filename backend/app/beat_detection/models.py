from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BeatInfo:
    time: float
    beat_num: int


@dataclass
class BarInfo:
    start: float
    end: float
    bar_num: int


@dataclass
class BeatDetectionResult:
    beats: list[BeatInfo]
    bars: list[BarInfo]
    tempo: float

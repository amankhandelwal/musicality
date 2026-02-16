from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GenreHint(str, Enum):
    SALSA = "salsa"
    BACHATA = "bachata"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InstrumentTemplate:
    name: str
    display_name: str
    stem: str          # drums, bass, vocals, other
    freq_band: str     # low, mid, high


@dataclass(frozen=True)
class FrequencyBand:
    name: str
    low_hz: float
    high_hz: float


FREQ_BANDS: dict[str, tuple[float, float]] = {
    "low": (20, 500),
    "low_mid": (500, 2000),
    "mid": (500, 4000),
    "mid_high": (2000, 6000),
    "high": (4000, 16000),
}

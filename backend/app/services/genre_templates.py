"""Genre-specific instrument templates for onset-based analysis.

Each template defines which instruments are expected in a genre, which Demucs
stem they live in, and their frequency band for sub-stem attribution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentTemplate:
    name: str
    display_name: str
    stem: str          # drums, bass, vocals, other
    freq_band: str     # low, mid, high


# Frequency band cutoffs (Hz) used for bandpass filtering
FREQ_BANDS = {
    "low": (20, 500),
    "low_mid": (500, 2000),
    "mid": (500, 4000),
    "mid_high": (2000, 6000),
    "high": (4000, 16000),
}


BACHATA_TEMPLATES: list[InstrumentTemplate] = [
    InstrumentTemplate(
        name="guira",
        display_name="Guira",
        stem="drums",
        freq_band="high",
    ),
    InstrumentTemplate(
        name="bongo",
        display_name="Bongo",
        stem="drums",
        freq_band="low",
    ),
    InstrumentTemplate(
        name="bass_guitar",
        display_name="Bass",
        stem="bass",
        freq_band="low",
    ),
    InstrumentTemplate(
        name="lead_guitar",
        display_name="Lead Gtr",
        stem="other",
        freq_band="high",
    ),
    InstrumentTemplate(
        name="rhythm_guitar",
        display_name="Rhy Gtr",
        stem="other",
        freq_band="mid",
    ),
    InstrumentTemplate(
        name="piano",
        display_name="Piano",
        stem="other",
        freq_band="mid",
    ),
    InstrumentTemplate(
        name="voice",
        display_name="Voice",
        stem="vocals",
        freq_band="mid",
    ),
]


SALSA_TEMPLATES: list[InstrumentTemplate] = [
    InstrumentTemplate(
        name="conga",
        display_name="Conga",
        stem="drums",
        freq_band="low",
    ),
    InstrumentTemplate(
        name="timbales",
        display_name="Timbales",
        stem="drums",
        freq_band="low_mid",
    ),
    InstrumentTemplate(
        name="cowbell",
        display_name="Cowbell",
        stem="drums",
        freq_band="mid_high",
    ),
    InstrumentTemplate(
        name="claves",
        display_name="Claves",
        stem="drums",
        freq_band="high",
    ),
    InstrumentTemplate(
        name="maracas_guiro",
        display_name="Maracas",
        stem="drums",
        freq_band="high",
    ),
    InstrumentTemplate(
        name="bass_guitar",
        display_name="Bass",
        stem="bass",
        freq_band="low",
    ),
    InstrumentTemplate(
        name="piano",
        display_name="Piano",
        stem="other",
        freq_band="mid",
    ),
    InstrumentTemplate(
        name="trumpet",
        display_name="Trumpet",
        stem="other",
        freq_band="high",
    ),
    InstrumentTemplate(
        name="trombone",
        display_name="Trombone",
        stem="other",
        freq_band="low",
    ),
    InstrumentTemplate(
        name="voice",
        display_name="Voice",
        stem="vocals",
        freq_band="mid",
    ),
]


def get_templates(genre: str) -> list[InstrumentTemplate]:
    """Return instrument templates for the given genre."""
    if genre == "bachata":
        return BACHATA_TEMPLATES
    elif genre == "salsa":
        return SALSA_TEMPLATES
    # Default to bachata
    return BACHATA_TEMPLATES

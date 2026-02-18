from __future__ import annotations

from app.genre.models import InstrumentTemplate


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
        stem="guitar",
        freq_band="high",
    ),
    InstrumentTemplate(
        name="rhythm_guitar",
        display_name="Rhy Gtr",
        stem="guitar",
        freq_band="mid",
    ),
    InstrumentTemplate(
        name="piano",
        display_name="Piano",
        stem="piano",
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
        stem="piano",
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


class StaticGenreTemplateProvider:
    def get_templates(self, genre: str) -> list[InstrumentTemplate]:
        if genre == "bachata":
            return BACHATA_TEMPLATES
        elif genre == "salsa":
            return SALSA_TEMPLATES
        return BACHATA_TEMPLATES

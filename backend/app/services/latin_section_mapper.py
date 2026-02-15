from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

from app.models import GenreHint

# Mapping generic labels to Latin dance section labels
# Bachata: derecho (straight), majao (chorus/hook), mambo (instrumental break)
# Salsa: tema (theme/verse), montuno (call-response), mambo (instrumental)

BACHATA_MAP = {
    "intro": "derecho",
    "verse": "derecho",
    "chorus": "majao",
    "bridge": "mambo",
    "instrumental": "mambo",
    "solo": "mambo",
    "outro": "derecho",
}

SALSA_MAP = {
    "intro": "tema",
    "verse": "tema",
    "chorus": "montuno",
    "bridge": "mambo",
    "instrumental": "mambo",
    "solo": "mambo",
    "outro": "montuno",
}


def map_sections(
    sections: list[dict],
    genre: GenreHint,
    stems_dir: str | None = None,
) -> list[dict]:
    """Map generic section labels to Latin dance labels.

    Uses stem energy analysis when stems are available to refine mappings.
    """
    label_map = BACHATA_MAP if genre == GenreHint.BACHATA else SALSA_MAP

    mapped = []
    for section in sections:
        generic_label = section["label"]
        latin_label = label_map.get(generic_label, "derecho" if genre == GenreHint.BACHATA else "tema")

        # Refine using stem energy if available
        if stems_dir:
            latin_label = _refine_with_stems(section, latin_label, stems_dir, genre)

        mapped.append({
            "start": section["start"],
            "end": section["end"],
            "label": generic_label,
            "latin_label": latin_label,
        })

    return mapped


def _refine_with_stems(
    section: dict, current_label: str, stems_dir: str, genre: GenreHint
) -> str:
    """Use stem energy to refine section classification."""
    try:
        stems_path = Path(stems_dir)
        start = section["start"]
        end = section["end"]
        duration = end - start
        if duration < 1.0:
            return current_label

        # Load stems for this section
        vocals_energy = _section_energy(stems_path / "vocals.wav", start, duration)
        drums_energy = _section_energy(stems_path / "drums.wav", start, duration)
        other_energy = _section_energy(stems_path / "other.wav", start, duration)

        # High instrumental energy + low vocals = mambo
        instrumental_ratio = (drums_energy + other_energy) / max(vocals_energy, 1e-6)

        if instrumental_ratio > 3.0:
            return "mambo"

        # High vocals + high energy = majao/montuno (chorus-like)
        if vocals_energy > 0.1 and drums_energy > 0.05:
            return "majao" if genre == GenreHint.BACHATA else "montuno"

        return current_label
    except Exception:
        return current_label


def _section_energy(audio_path: Path, start: float, duration: float) -> float:
    """Get RMS energy for a section of an audio file."""
    if not audio_path.exists():
        return 0.0
    try:
        y, sr = librosa.load(str(audio_path), sr=22050, offset=start, duration=duration, mono=True)
        return float(np.sqrt(np.mean(y**2)))
    except Exception:
        return 0.0

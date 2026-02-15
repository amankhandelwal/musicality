from __future__ import annotations

import logging
import tempfile
import traceback

from app.job_store import job_store
from app.models import (
    AnalysisResult,
    Bar,
    BarInstruments,
    Beat,
    GenreHint,
    InstrumentBeat,
    InstrumentGrid,
    JobStatus,
    Metadata,
    Section,
)
from app.services.beat_instrument_analyzer import analyze_instruments
from app.services.beat_tracker import detect_beats
from app.services.downloader import download_audio
from app.services.latin_section_mapper import map_sections
from app.services.section_analyzer import detect_sections
from app.services.source_separator import separate_stems

logger = logging.getLogger(__name__)


def guess_genre(title: str) -> GenreHint:
    """Guess genre from title keywords."""
    title_lower = title.lower()
    if any(w in title_lower for w in ["bachata", "romeo santos", "aventura", "prince royce"]):
        return GenreHint.BACHATA
    if any(w in title_lower for w in ["salsa", "timba", "son", "mambo"]):
        return GenreHint.SALSA
    return GenreHint.BACHATA  # Default to bachata


def run_pipeline(job_id: str) -> None:
    """Run the full analysis pipeline for a job."""
    job = job_store.get(job_id)
    if not job:
        return

    try:
        # Stage 1: Download (skip if audio already cached for this video)
        job_store.update_status(job_id, JobStatus.DOWNLOADING, 0.05)
        cached_audio = job_store.get_audio_cache(job.video_id) if job.video_id else None
        if cached_audio:
            import os
            audio_path, title, duration = cached_audio
            if not os.path.exists(audio_path):
                cached_audio = None

        if not cached_audio:
            output_dir = tempfile.mkdtemp(prefix="musicality_")
            audio_path, title, duration = download_audio(job.url, output_dir)
            if job.video_id:
                job_store.set_audio_cache(job.video_id, audio_path, title, duration)

        job.audio_path = audio_path
        genre = guess_genre(title)

        # Stage 2: Beat detection
        job_store.update_status(job_id, JobStatus.DETECTING_BEATS, 0.15)
        beats_raw, bars_raw, tempo = detect_beats(audio_path)

        # Stage 3: Source separation
        job_store.update_status(job_id, JobStatus.SEPARATING_STEMS, 0.30)
        try:
            stems_dir = separate_stems(audio_path)
            job.stems_dir = stems_dir
        except Exception as e:
            logger.warning(f"Source separation failed, continuing without stems: {e}")
            stems_dir = None

        # Stage 4: Section detection
        job_store.update_status(job_id, JobStatus.DETECTING_SECTIONS, 0.55)
        sections_raw = detect_sections(audio_path)

        # Stage 5: Latin section mapping
        job_store.update_status(job_id, JobStatus.MAPPING_SECTIONS, 0.65)
        sections_mapped = map_sections(sections_raw, genre, stems_dir)

        # Stage 6: Beat-by-beat instrument analysis
        job_store.update_status(job_id, JobStatus.ANALYZING_INSTRUMENTS, 0.75)
        grid_raw = analyze_instruments(
            genre.value, bars_raw, beats_raw, stems_dir, tempo
        )

        # Build result
        instrument_grid = InstrumentGrid(
            genre=grid_raw["genre"],
            instrument_list=grid_raw["instrument_list"],
            subdivisions=grid_raw.get("subdivisions", 16),
            bars=[
                BarInstruments(
                    bar_num=b["bar_num"],
                    instruments=[InstrumentBeat(**ib) for ib in b["instruments"]],
                )
                for b in grid_raw["bars"]
            ],
        )

        result = AnalysisResult(
            metadata=Metadata(title=title, duration=duration, genre_hint=genre),
            tempo=tempo,
            beats=[Beat(**b) for b in beats_raw],
            bars=[Bar(**b) for b in bars_raw],
            sections=[Section(**s) for s in sections_mapped],
            instrument_grid=instrument_grid,
        )

        job_store.set_result(job_id, result)

    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {traceback.format_exc()}")
        job_store.set_error(job_id, str(e))

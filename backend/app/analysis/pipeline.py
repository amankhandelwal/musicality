from __future__ import annotations

import logging
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor

from app.analysis.models import (
    AnalysisResult,
    Bar,
    BarInstruments,
    Beat,
    InstrumentBeat,
    InstrumentGrid,
    Metadata,
)
from app.genre.models import GenreHint
from app.jobs.models import JobStatus

logger = logging.getLogger(__name__)


def guess_genre(title: str) -> GenreHint:
    """Guess genre from title keywords."""
    title_lower = title.lower()
    if any(w in title_lower for w in ["bachata", "romeo santos", "aventura", "prince royce"]):
        return GenreHint.BACHATA
    if any(w in title_lower for w in ["salsa", "timba", "son", "mambo"]):
        return GenreHint.SALSA
    return GenreHint.BACHATA


class AnalysisPipeline:
    def __init__(
        self,
        downloader: object,
        separator: object,
        beat_detector: object,
        instrument_analyzer: object,
        job_repository: object,
    ) -> None:
        self._downloader = downloader
        self._separator = separator
        self._beat_detector = beat_detector
        self._instrument_analyzer = instrument_analyzer
        self._job_repo = job_repository

    def run(self, job_id: str) -> None:
        """Run the full analysis pipeline for a job."""
        job = self._job_repo.get(job_id)
        if not job:
            return

        try:
            # Stage 1: Download
            self._job_repo.update_status(job_id, JobStatus.DOWNLOADING, 0.05)
            cached_audio = self._job_repo.get_audio_cache(job.video_id) if job.video_id else None
            if cached_audio:
                import os
                audio_path, title, duration = cached_audio
                if not os.path.exists(audio_path):
                    cached_audio = None

            if not cached_audio:
                output_dir = tempfile.mkdtemp(prefix="musicality_")
                download_result = self._downloader.download(job.url, output_dir)
                audio_path = download_result.audio_path
                title = download_result.title
                duration = download_result.duration
                if job.video_id:
                    self._job_repo.set_audio_cache(job.video_id, audio_path, title, duration)

            job.audio_path = audio_path
            genre = job.genre if job.genre else guess_genre(title)

            # Stages 2-3: Beat detection + source separation (parallel)
            self._job_repo.update_status(job_id, JobStatus.SEPARATING_STEMS, 0.15)

            with ThreadPoolExecutor(max_workers=2) as pool:
                beat_future = pool.submit(self._beat_detector.detect, audio_path)
                stem_future = pool.submit(self._separator.separate, audio_path)

                beat_result = beat_future.result()
                beats_raw = [{"time": b.time, "beat_num": b.beat_num} for b in beat_result.beats]
                bars_raw = [{"start": b.start, "end": b.end, "bar_num": b.bar_num} for b in beat_result.bars]
                tempo = beat_result.tempo

                try:
                    sep_result = stem_future.result()
                    stems_dir = sep_result.stems_dir
                    job.stems_dir = stems_dir
                except Exception as e:
                    logger.warning(f"Source separation failed, continuing without stems: {e}")
                    stems_dir = None

            # Stage 4: Beat-by-beat instrument analysis
            self._job_repo.update_status(job_id, JobStatus.ANALYZING_INSTRUMENTS, 0.75)
            grid_raw = self._instrument_analyzer.analyze(
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
                instrument_grid=instrument_grid,
            )

            self._job_repo.set_result(job_id, result)

        except Exception as e:
            logger.error(f"Pipeline failed for job {job_id}: {traceback.format_exc()}")
            self._job_repo.set_error(job_id, str(e))

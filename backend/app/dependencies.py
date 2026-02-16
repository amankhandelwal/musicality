"""Dependency Injection wiring for FastAPI.

Change one line here to swap any implementation
(e.g., MadmomBeatDetector -> LibrosaBeatDetector).
"""

from __future__ import annotations

from functools import lru_cache

from app.analysis.pipeline import AnalysisPipeline
from app.analysis.service import AnalysisService
from app.beat_detection.madmom_detector import MadmomBeatDetector
from app.downloader.ytdlp_downloader import YtDlpAudioDownloader
from app.genre.static_provider import StaticGenreTemplateProvider
from app.instrument_analysis.onset_analyzer import OnsetInstrumentAnalyzer
from app.jobs.in_memory_repository import InMemoryJobRepository
from app.separator.demucs_separator import DemucsSourceSeparator


@lru_cache
def get_job_repository() -> InMemoryJobRepository:
    return InMemoryJobRepository()


@lru_cache
def get_downloader() -> YtDlpAudioDownloader:
    return YtDlpAudioDownloader()


@lru_cache
def get_separator() -> DemucsSourceSeparator:
    return DemucsSourceSeparator()


@lru_cache
def get_beat_detector() -> MadmomBeatDetector:
    return MadmomBeatDetector()


@lru_cache
def get_template_provider() -> StaticGenreTemplateProvider:
    return StaticGenreTemplateProvider()


@lru_cache
def get_instrument_analyzer() -> OnsetInstrumentAnalyzer:
    return OnsetInstrumentAnalyzer(template_provider=get_template_provider())


@lru_cache
def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(
        downloader=get_downloader(),
        separator=get_separator(),
        beat_detector=get_beat_detector(),
        instrument_analyzer=get_instrument_analyzer(),
        job_repository=get_job_repository(),
    )


@lru_cache
def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        pipeline=get_pipeline(),
        job_repository=get_job_repository(),
    )

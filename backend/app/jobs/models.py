from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DETECTING_BEATS = "detecting_beats"
    SEPARATING_STEMS = "separating_stems"
    ANALYZING_INSTRUMENTS = "analyzing_instruments"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Job:
    job_id: str
    url: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    error: str | None = None
    result: object | None = None
    video_id: str | None = None
    genre: object | None = None
    audio_path: str | None = None
    stems_dir: str | None = None
    created_at: float = field(default_factory=time.time)

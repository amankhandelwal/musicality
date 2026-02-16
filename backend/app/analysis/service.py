from __future__ import annotations

import re
import threading
import uuid

from app.analysis.pipeline import AnalysisPipeline
from app.jobs.models import JobStatus

VIDEO_ID_PATTERNS = [
    re.compile(r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})"),
]

MAX_CONCURRENT_JOBS = 2


def extract_video_id(url: str) -> str | None:
    for pattern in VIDEO_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


class AnalysisService:
    def __init__(self, pipeline: AnalysisPipeline, job_repository: object) -> None:
        self._pipeline = pipeline
        self._job_repo = job_repository

    def submit(self, url: str, genre: object | None = None) -> dict[str, str]:
        """Submit a URL for analysis. Returns {"job_id": ...} or raises."""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        genre_key = genre.value if genre else "auto"
        cache_key = f"{video_id}:{genre_key}"

        cached_job_id = self._job_repo.get_cached_job_id(cache_key)
        if cached_job_id:
            cached = self._job_repo.get(cached_job_id)
            if cached and cached.status == JobStatus.COMPLETE:
                return {"job_id": cached_job_id}
            if cached and cached.status == JobStatus.FAILED:
                self._job_repo.remove(cached_job_id, cache_key)

        if self._job_repo.active_count >= MAX_CONCURRENT_JOBS:
            raise RuntimeError("Too many active jobs. Try again later.")

        job_id = uuid.uuid4().hex[:12]
        job = self._job_repo.create(job_id, url)
        job.video_id = video_id
        job.genre = genre
        self._job_repo.set_cache(cache_key, job_id)

        thread = threading.Thread(target=self._pipeline.run, args=(job_id,), daemon=True)
        thread.start()

        return {"job_id": job_id}

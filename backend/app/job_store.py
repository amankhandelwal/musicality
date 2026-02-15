from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from app.models import AnalysisResult, JobStatus


@dataclass
class Job:
    job_id: str
    url: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    error: str | None = None
    result: AnalysisResult | None = None
    video_id: str | None = None
    audio_path: str | None = None
    stems_dir: str | None = None
    created_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._cache: dict[str, str] = {}  # video_id -> job_id
        self._audio_cache: dict[str, tuple[str, str, float]] = {}  # video_id -> (path, title, duration)

    def create(self, job_id: str, url: str) -> Job:
        job = Job(job_id=job_id, url=url)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus, progress: float | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status
                if progress is not None:
                    job.progress = progress

    def set_error(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.error = error

    def set_result(self, job_id: str, result: AnalysisResult) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.COMPLETE
                job.progress = 1.0
                job.result = result

    def remove(self, job_id: str, video_id: str | None = None) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)
            if video_id and video_id in self._cache:
                del self._cache[video_id]

    def get_cached_job_id(self, video_id: str) -> str | None:
        with self._lock:
            return self._cache.get(video_id)

    def set_cache(self, video_id: str, job_id: str) -> None:
        with self._lock:
            self._cache[video_id] = job_id

    def get_audio_cache(self, video_id: str) -> tuple[str, str, float] | None:
        with self._lock:
            return self._audio_cache.get(video_id)

    def set_audio_cache(self, video_id: str, audio_path: str, title: str, duration: float) -> None:
        with self._lock:
            self._audio_cache[video_id] = (audio_path, title, duration)

    def cleanup_old(self, max_age_seconds: float = 3600) -> list[str]:
        now = time.time()
        to_remove = []
        with self._lock:
            for jid, job in list(self._jobs.items()):
                if now - job.created_at > max_age_seconds:
                    to_remove.append(jid)
                    if job.video_id and job.video_id in self._cache:
                        del self._cache[job.video_id]
                    del self._jobs[jid]
        return to_remove

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(
                1 for j in self._jobs.values()
                if j.status not in (JobStatus.COMPLETE, JobStatus.FAILED)
            )


job_store = JobStore()

from __future__ import annotations

import re
import threading
import uuid

from fastapi import APIRouter, HTTPException

from app.job_store import job_store
from app.models import AnalyzeRequest, JobStatus
from app.pipeline import run_pipeline

router = APIRouter()

MAX_CONCURRENT_JOBS = 2

VIDEO_ID_PATTERNS = [
    re.compile(r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})"),
]


def extract_video_id(url: str) -> str | None:
    for pattern in VIDEO_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


@router.post("/analyze")
def start_analysis(req: AnalyzeRequest) -> dict[str, str]:
    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    genre_key = req.genre.value if req.genre else "auto"
    cache_key = f"{video_id}:{genre_key}"

    cached_job_id = job_store.get_cached_job_id(cache_key)
    if cached_job_id:
        cached = job_store.get(cached_job_id)
        if cached and cached.status == JobStatus.COMPLETE:
            return {"job_id": cached_job_id}
        # Stale/failed cache entry — clear it so we can re-run
        if cached and cached.status == JobStatus.FAILED:
            job_store.remove(cached_job_id, cache_key)

    if job_store.active_count >= MAX_CONCURRENT_JOBS:
        raise HTTPException(status_code=429, detail="Too many active jobs. Try again later.")

    job_id = uuid.uuid4().hex[:12]
    job = job_store.create(job_id, req.url)
    job.video_id = video_id
    job.genre = req.genre
    job_store.set_cache(cache_key, job_id)

    thread = threading.Thread(target=run_pipeline, args=(job_id,), daemon=True)
    thread.start()

    return {"job_id": job_id}

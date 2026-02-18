from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.dependencies import get_job_repository
from app.jobs.in_memory_repository import InMemoryJobRepository

router = APIRouter()


@router.get("/audio/{job_id}")
def get_audio(
    job_id: str,
    job_repo: InMemoryJobRepository = Depends(get_job_repository),
) -> FileResponse:
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.audio_path or not Path(job.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio not ready")
    return FileResponse(
        job.audio_path,
        media_type="audio/wav",
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/audio/{job_id}/stems/{stem_name}")
def get_stem(
    job_id: str,
    stem_name: Literal["drums", "bass", "vocals", "guitar", "piano", "other"],
    job_repo: InMemoryJobRepository = Depends(get_job_repository),
) -> FileResponse:
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.stems_dir:
        raise HTTPException(status_code=404, detail="Stems not available")
    stem_path = Path(job.stems_dir) / f"{stem_name}.wav"
    if not stem_path.exists():
        raise HTTPException(status_code=404, detail=f"Stem '{stem_name}' not found")
    return FileResponse(
        str(stem_path),
        media_type="audio/wav",
        headers={"Accept-Ranges": "bytes"},
    )

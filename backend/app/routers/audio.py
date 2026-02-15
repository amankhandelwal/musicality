from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.job_store import job_store

router = APIRouter()


@router.get("/audio/{job_id}")
def get_audio(job_id: str) -> FileResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.audio_path or not Path(job.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio not ready")
    return FileResponse(
        job.audio_path,
        media_type="audio/wav",
        headers={"Accept-Ranges": "bytes"},
    )

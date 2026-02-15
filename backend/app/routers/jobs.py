from fastapi import APIRouter, HTTPException

from app.job_store import job_store
from app.models import JobResponse

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> JobResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        result=job.result,
    )

import asyncio

from fastapi import APIRouter, HTTPException, Query

from app.job_store import job_store
from app.models import JobResponse, JobStatus

router = APIRouter()

LONG_POLL_TIMEOUT = 30.0  # seconds
LONG_POLL_INTERVAL = 0.5  # check every 500ms


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    after_status: str | None = Query(None),
    after_progress: float | None = Query(None),
) -> JobResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Long-poll: hold the request until status or progress changes
    if after_status is not None:
        elapsed = 0.0
        while elapsed < LONG_POLL_TIMEOUT:
            if job.status.value != after_status:
                break
            if after_progress is not None and job.progress != after_progress:
                break
            if job.status in (JobStatus.COMPLETE, JobStatus.FAILED):
                break
            await asyncio.sleep(LONG_POLL_INTERVAL)
            elapsed += LONG_POLL_INTERVAL

    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        result=job.result,
    )

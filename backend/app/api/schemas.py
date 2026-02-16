from __future__ import annotations

from pydantic import BaseModel

from app.analysis.models import AnalysisResult
from app.genre.models import GenreHint
from app.jobs.models import JobStatus


class AnalyzeRequest(BaseModel):
    url: str
    genre: GenreHint | None = None


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    error: str | None = None
    result: AnalysisResult | None = None

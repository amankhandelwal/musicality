from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.analysis.service import AnalysisService
from app.api.schemas import AnalyzeRequest
from app.dependencies import get_analysis_service

router = APIRouter()


@router.post("/analyze")
def start_analysis(
    req: AnalyzeRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, str]:
    try:
        return service.submit(req.url, req.genre)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze, audio, jobs

app = FastAPI(title="Musicality", description="Salsa/Bachata music visualization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(jobs.router)
app.include_router(audio.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

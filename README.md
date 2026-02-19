# Musicality

Salsa and Bachata music analysis and visualization tool. Paste a YouTube URL and get a beat-by-beat instrument grid, stem player, and rhythmic breakdown.

## Features

- **Beat detection** — Madmom-based beat and bar tracking
- **Source separation** — Demucs 6-stem splitting (drums, bass, vocals, guitar, piano, other)
- **Instrument grid** — Visual beat grid showing instrument activity per bar
- **Stem player** — Mute/solo individual instruments during playback
- **Genre awareness** — Salsa and Bachata templates with genre-specific frequency bands

## Prerequisites

| Tool | Version | macOS install |
|------|---------|---------------|
| Python | 3.10–3.12 | `brew install python@3.12` |
| Node.js | 18+ | `brew install node` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| FFmpeg | any | `brew install ffmpeg` |
| Make | any | Xcode CLI Tools (`xcode-select --install`) |

## Quick Start

```bash
./setup.sh          # check prerequisites, install all dependencies
make start-be       # start backend at http://localhost:8000
make start-fe       # start frontend at http://localhost:5173
```

Stop everything with `make stop`.

## Development

### Backend

```bash
cd backend
uv sync                                          # install/update deps
uv run uvicorn app.main:app --reload --port 8000 # start dev server
```

### Frontend

```bash
cd frontend
npm install          # install/update deps
npm run dev          # start Vite dev server
```

## Project Structure

```
musicality/
├── Makefile                 # start-be, start-fe, stop
├── setup.sh                 # one-command setup
├── backend/
│   ├── pyproject.toml       # Python deps (uv)
│   └── app/
│       ├── main.py          # FastAPI app + CORS
│       ├── dependencies.py  # dependency injection
│       ├── routers/         # analyze, jobs, audio, health
│       ├── analysis/        # pipeline, service, models
│       ├── beat_detection/  # madmom beat/bar detection
│       ├── separator/       # Demucs stem separation
│       ├── instrument_analysis/  # onset + grid analysis
│       ├── downloader/      # yt-dlp audio download
│       └── genre/           # salsa/bachata templates
└── frontend/
    ├── package.json         # React + Vite
    └── src/
        ├── App.tsx          # root component
        ├── api/             # API client
        ├── components/      # UI components
        ├── hooks/           # analysis, stem player, beat sync
        ├── pages/           # landing, results
        └── types/           # TypeScript interfaces
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Submit a YouTube URL for analysis. Body: `{ url, genre? }` |
| `GET` | `/jobs/{job_id}` | Poll job status (supports long-polling via `after_status`) |
| `GET` | `/audio/{job_id}` | Download processed audio (WAV) |
| `GET` | `/audio/{job_id}/stems/{stem_name}` | Download an individual stem (`drums`, `bass`, `vocals`, `guitar`, `piano`, `other`) |
| `GET` | `/health` | Health check — returns `{ "status": "ok" }` |

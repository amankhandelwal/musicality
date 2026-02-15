from __future__ import annotations

import tempfile
from pathlib import Path

import yt_dlp


def download_audio(url: str, output_dir: str | None = None) -> tuple[str, str, float]:
    """Download audio from YouTube URL. Returns (audio_path, title, duration)."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="musicality_")

    output_path = str(Path(output_dir) / "audio.wav")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(Path(output_dir) / "audio.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "Unknown")
        duration = float(info.get("duration", 0))

    return output_path, title, duration

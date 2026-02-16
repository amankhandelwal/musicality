from __future__ import annotations

import tempfile
from pathlib import Path

import yt_dlp

from app.downloader.models import DownloadResult


class YtDlpAudioDownloader:
    def download(self, url: str, output_dir: str | None = None) -> DownloadResult:
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

        return DownloadResult(audio_path=output_path, title=title, duration=duration)

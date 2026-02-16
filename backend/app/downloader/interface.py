from __future__ import annotations

from typing import Protocol

from app.downloader.models import DownloadResult


class AudioDownloader(Protocol):
    def download(self, url: str, output_dir: str | None = None) -> DownloadResult: ...

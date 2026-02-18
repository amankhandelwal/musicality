from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.separator.models import SeparationResult


class DemucsSourceSeparator:
    def separate(self, audio_path: str, output_dir: str | None = None) -> SeparationResult:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="musicality_stems_")

        cmd = [
            "python", "-m", "demucs",
            "-n", "htdemucs_6s",
            "--segment", "7",
            "-o", output_dir,
            audio_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)

        audio_name = Path(audio_path).stem
        stems_dir = str(Path(output_dir) / "htdemucs_6s" / audio_name)

        return SeparationResult(stems_dir=stems_dir)

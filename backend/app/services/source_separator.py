from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def separate_stems(audio_path: str, output_dir: str | None = None) -> str:
    """Run Demucs v4 source separation.

    Returns the directory containing separated stems (drums.wav, bass.wav, vocals.wav, other.wav).
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="musicality_stems_")

    cmd = [
        "python", "-m", "demucs",
        "--two-stems=vocals",  # First pass isn't needed; we use htdemucs_ft for 4 stems
    ]

    # Use htdemucs for 4-stem separation
    cmd = [
        "python", "-m", "demucs",
        "-n", "htdemucs",
        "--segment", "7",  # Process in 7s segments (htdemucs max is 7.8)
        "-o", output_dir,
        audio_path,
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    # Demucs outputs to output_dir/htdemucs/audio/
    audio_name = Path(audio_path).stem
    stems_dir = str(Path(output_dir) / "htdemucs" / audio_name)

    return stems_dir

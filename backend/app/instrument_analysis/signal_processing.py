"""Signal processing helpers for instrument analysis.

Bandpass filtering, onset velocity computation, spectral pitch,
energy attribution, onset snapping, and stem loading.
"""

from __future__ import annotations

import logging
from pathlib import Path

import librosa
import numpy as np
from scipy.signal import butter, sosfilt

from app.genre.models import FREQ_BANDS, InstrumentTemplate

logger = logging.getLogger(__name__)

ONSET_WINDOW_SEC = 0.050
ENERGY_RATIO_THRESHOLD = 0.4
PRESENCE_THRESHOLD = 0.005
SNAP_TOLERANCE = 0.4
SPECTRAL_WINDOW_SEC = 0.050


def bandpass_filter(
    signal: np.ndarray, sr: int, low_hz: float, high_hz: float
) -> np.ndarray:
    """Apply a Butterworth bandpass filter."""
    nyquist = sr / 2.0
    low = max(low_hz / nyquist, 0.001)
    high = min(high_hz / nyquist, 0.999)

    if low >= high:
        return signal

    try:
        sos = butter(4, [low, high], btype="band", output="sos")
        return sosfilt(sos, signal)
    except Exception:
        return signal


def compute_onset_velocity(
    onset_time: float,
    onset_env: np.ndarray | None,
    sr: int,
    hop: int,
) -> float:
    """Look up onset strength and return normalized 0.0-1.0 velocity."""
    if onset_env is None or len(onset_env) == 0:
        return 0.7

    frame = int(onset_time * sr / hop)
    frame = max(0, min(frame, len(onset_env) - 1))
    strength = onset_env[frame]

    max_val = onset_env.max()
    if max_val <= 0:
        return 0.7

    normalized = strength / max_val
    compressed = float(np.power(normalized, 0.7))
    return round(max(0.0, min(1.0, compressed)), 3)


def compute_spectral_pitch(
    bp_signal: np.ndarray,
    sr: int,
    onset_time: float,
    freq_band: str,
) -> float:
    """Compute spectral centroid in a window around onset, normalized within freq band."""
    half_win = int(SPECTRAL_WINDOW_SEC * sr / 2)
    center = int(onset_time * sr)
    start = max(0, center - half_win)
    end = min(len(bp_signal), center + half_win)

    if end <= start:
        return 0.5

    window = bp_signal[start:end]
    if np.max(np.abs(window)) < 1e-8:
        return 0.5

    centroid = librosa.feature.spectral_centroid(y=window, sr=sr, n_fft=min(len(window), 1024))
    centroid_hz = float(np.mean(centroid))

    freq_low, freq_high = FREQ_BANDS[freq_band]
    band_range = freq_high - freq_low
    if band_range <= 0:
        return 0.5

    normalized = (centroid_hz - freq_low) / band_range
    return round(max(0.0, min(1.0, normalized)), 3)


def has_energy_at_onset(
    bp_signal: np.ndarray,
    sr: int,
    onset_time: float,
    this_freq_band: str,
    stem_name: str,
    bandpass_cache: dict[tuple[str, str], np.ndarray],
    stem_templates: dict[str, list[InstrumentTemplate]],
) -> bool:
    """Check if a bandpass-filtered signal has enough energy at an onset time."""
    half_win = int(ONSET_WINDOW_SEC * sr / 2)
    center = int(onset_time * sr)
    start = max(0, center - half_win)
    end = min(len(bp_signal), center + half_win)

    if end <= start:
        return False

    this_rms = np.sqrt(np.mean(bp_signal[start:end] ** 2))
    if this_rms < PRESENCE_THRESHOLD:
        return False

    seen_bands = {this_freq_band}
    max_rms = this_rms
    for t in stem_templates.get(stem_name, []):
        if t.freq_band in seen_bands:
            continue
        seen_bands.add(t.freq_band)
        other_key = (stem_name, t.freq_band)
        other_bp = bandpass_cache.get(other_key)
        if other_bp is not None:
            other_start = max(0, center - half_win)
            other_end = min(len(other_bp), center + half_win)
            if other_end > other_start:
                other_rms = np.sqrt(np.mean(other_bp[other_start:other_end] ** 2))
                max_rms = max(max_rms, other_rms)

    return (this_rms / max_rms) >= ENERGY_RATIO_THRESHOLD if max_rms > 0 else False


def snap_to_subdivision(
    onset_time: float,
    subdiv_times: list[float],
    cycle_end: float,
) -> int:
    """Snap an onset time to the nearest subdivision index."""
    best_idx = -1
    best_dist = float("inf")
    for i, st in enumerate(subdiv_times):
        dist = abs(onset_time - st)
        if dist < best_dist:
            best_dist = dist
            best_idx = i

    if best_idx >= 0:
        if best_idx + 1 < len(subdiv_times):
            subdiv_dur = subdiv_times[best_idx + 1] - subdiv_times[best_idx]
        else:
            subdiv_dur = cycle_end - subdiv_times[best_idx]
        if subdiv_dur > 0 and best_dist / subdiv_dur > SNAP_TOLERANCE:
            return -1

    return best_idx


def load_stems(stems_dir: str) -> dict[str, tuple[np.ndarray, int]]:
    """Load all available stem audio files."""
    stems = {}
    stems_path = Path(stems_dir)
    for stem_name in ["drums", "bass", "vocals", "guitar", "piano", "other"]:
        stem_file = stems_path / f"{stem_name}.wav"
        if stem_file.exists():
            try:
                y, sr = librosa.load(str(stem_file), sr=22050, mono=True)
                stems[stem_name] = (y, sr)
            except Exception as e:
                logger.warning(f"Failed to load stem {stem_name}: {e}")
    return stems

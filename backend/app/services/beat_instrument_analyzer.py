"""Beat-by-beat instrument analyzer using onset detection.

Uses librosa onset detection on Demucs stems with bandpass-filtered sub-stem
attribution to produce 16-subdivision instrument grids that vary per bar.
"""

from __future__ import annotations

import logging
from pathlib import Path

import librosa
import numpy as np
from scipy.signal import butter, sosfilt

from app.services.genre_templates import FREQ_BANDS, InstrumentTemplate, get_templates

logger = logging.getLogger(__name__)

NUM_SUBDIVISIONS = 16
ONSET_WINDOW_SEC = 0.030  # 30ms window for sub-stem energy attribution
ENERGY_RATIO_THRESHOLD = 0.3  # min energy ratio to attribute onset to sub-stem
PRESENCE_THRESHOLD = 0.005  # below this, stem has negligible energy
SNAP_TOLERANCE = 0.5  # max fraction of subdivision duration to snap


def analyze_instruments(
    genre: str,
    bars: list[dict],
    beats: list[dict],
    stems_dir: str | None,
    tempo: float,
) -> dict:
    """Analyze instruments beat-by-beat across all 8-count cycles.

    Returns dict matching InstrumentGrid schema:
        {"genre": str, "instrument_list": [str], "subdivisions": 16, "bars": [...]}
    """
    templates = get_templates(genre)
    instrument_names = [t.name for t in templates]

    cycles = _pair_bars_into_cycles(bars)

    if not cycles or not stems_dir:
        return _empty_result(genre, templates, cycles)

    stems_audio = _load_stems(stems_dir)
    if not stems_audio:
        return _empty_result(genre, templates, cycles)

    # Precompute onset times for each stem (whole song, once)
    # Detecting on the full envelope gives librosa proper adaptive thresholding
    stem_onset_times: dict[str, np.ndarray] = {}
    hop = 512
    for stem_name, (y, sr) in stems_audio.items():
        env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=env,
            sr=sr,
            hop_length=hop,
            backtrack=False,
        )
        times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)
        stem_onset_times[stem_name] = times
        logger.info("Stem '%s': %d onsets detected across full song", stem_name, len(times))

    # Precompute bandpass-filtered stems for each unique (stem, freq_band) pair
    bandpass_cache: dict[tuple[str, str], np.ndarray] = {}
    for t in templates:
        key = (t.stem, t.freq_band)
        if key not in bandpass_cache and t.stem in stems_audio:
            y, sr = stems_audio[t.stem]
            freq_low, freq_high = FREQ_BANDS[t.freq_band]
            bandpass_cache[key] = _bandpass_filter(y, sr, freq_low, freq_high)

    # Group templates by stem for multi-instrument attribution
    stem_templates: dict[str, list[InstrumentTemplate]] = {}
    for t in templates:
        stem_templates.setdefault(t.stem, []).append(t)

    # Build beat time list for subdivision grid computation
    beat_times = [b["time"] for b in beats]

    result_bars = []
    for cycle_num, (cycle_start, cycle_end) in enumerate(cycles):
        subdiv_times = _build_subdivision_grid(
            cycle_start, cycle_end, beat_times
        )

        cycle_instruments = _analyze_cycle_onsets(
            cycle_num,
            cycle_start,
            cycle_end,
            subdiv_times,
            templates,
            stem_templates,
            stems_audio,
            stem_onset_times,
            bandpass_cache,
        )

        result_bars.append({
            "bar_num": cycle_num,
            "instruments": cycle_instruments,
        })

    return {
        "genre": genre,
        "instrument_list": instrument_names,
        "subdivisions": NUM_SUBDIVISIONS,
        "bars": result_bars,
    }


def _pair_bars_into_cycles(bars: list[dict]) -> list[tuple[float, float]]:
    """Pair consecutive 4/4 bars into 8-count dance cycles."""
    cycles = []
    i = 0
    while i + 1 < len(bars):
        cycle_start = bars[i]["start"]
        cycle_end = bars[i + 1]["end"]
        cycles.append((cycle_start, cycle_end))
        i += 2
    if i < len(bars):
        cycles.append((bars[i]["start"], bars[i]["end"]))
    return cycles


def _build_subdivision_grid(
    cycle_start: float,
    cycle_end: float,
    beat_times: list[float],
) -> list[float]:
    """Build 16 subdivision timestamps for an 8-count cycle.

    Uses actual beat times within the cycle. For each beat, the "&" position
    is the midpoint to the next beat (handles tempo drift naturally).
    Falls back to uniform spacing if fewer than 2 beats found in the cycle.
    """
    # Find beats within this cycle
    cycle_beats = [t for t in beat_times if cycle_start <= t < cycle_end]

    if len(cycle_beats) < 2:
        # Uniform fallback
        step = (cycle_end - cycle_start) / NUM_SUBDIVISIONS
        return [cycle_start + i * step for i in range(NUM_SUBDIVISIONS)]

    subdivs = []
    for i, bt in enumerate(cycle_beats):
        subdivs.append(bt)  # on-beat
        if i + 1 < len(cycle_beats):
            subdivs.append((bt + cycle_beats[i + 1]) / 2.0)  # "&"
        else:
            # Last beat: estimate "&" from previous beat spacing
            if i > 0:
                gap = bt - cycle_beats[i - 1]
            else:
                gap = (cycle_end - cycle_start) / 8.0
            subdivs.append(bt + gap / 2.0)

    # Pad or trim to exactly 16
    if len(subdivs) < NUM_SUBDIVISIONS:
        # Extend with uniform spacing from last subdivision
        last = subdivs[-1]
        remaining = NUM_SUBDIVISIONS - len(subdivs)
        gap = (cycle_end - last) / (remaining + 1)
        for j in range(1, remaining + 1):
            subdivs.append(last + j * gap)
    subdivs = subdivs[:NUM_SUBDIVISIONS]

    return subdivs


def _analyze_cycle_onsets(
    cycle_num: int,
    cycle_start: float,
    cycle_end: float,
    subdiv_times: list[float],
    templates: list[InstrumentTemplate],
    stem_templates: dict[str, list[InstrumentTemplate]],
    stems_audio: dict[str, tuple[np.ndarray, int]],
    stem_onset_times: dict[str, np.ndarray],
    bandpass_cache: dict[tuple[str, str], np.ndarray],
) -> list[dict]:
    """Analyze all instruments for a single cycle using onset detection."""
    # Filter precomputed onset times to this cycle's time range
    cycle_onsets: dict[str, list[float]] = {}
    for stem_name, all_onsets in stem_onset_times.items():
        mask = (all_onsets >= cycle_start) & (all_onsets < cycle_end)
        cycle_onsets[stem_name] = list(all_onsets[mask])

    # Build instrument patterns
    instruments = []
    for template in templates:
        if template.stem not in stems_audio:
            continue

        onsets = cycle_onsets.get(template.stem, [])
        # Check how many unique freq bands this stem has (not just template count)
        stem_bands = {t.freq_band for t in stem_templates.get(template.stem, [])}
        is_single_band = len(stem_bands) <= 1

        pattern = [False] * NUM_SUBDIVISIONS
        _, sr = stems_audio[template.stem]

        for onset_time in onsets:
            subdiv_idx = _snap_to_subdivision(onset_time, subdiv_times, cycle_end)
            if subdiv_idx < 0 or subdiv_idx >= NUM_SUBDIVISIONS:
                continue

            if is_single_band:
                # All instruments on this stem share the same band — can't
                # distinguish, so attribute onset to all of them
                pattern[subdiv_idx] = True
            else:
                bp_key = (template.stem, template.freq_band)
                bp_signal = bandpass_cache.get(bp_key)
                if bp_signal is None:
                    continue

                if _has_energy_at_onset(
                    bp_signal, sr, onset_time, template.freq_band,
                    template.stem, bandpass_cache, stem_templates,
                ):
                    pattern[subdiv_idx] = True

        if any(pattern):
            instruments.append({
                "instrument": template.name,
                "beats": pattern,
                "confidence": 0.7,
            })

    if cycle_num == 0:
        logger.info(
            "Cycle 0: %d onsets across stems %s → %d instruments",
            sum(len(v) for v in cycle_onsets.values()),
            {k: len(v) for k, v in cycle_onsets.items()},
            len(instruments),
        )

    return instruments


def _snap_to_subdivision(
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

    # Check snap tolerance: don't snap if too far from any subdivision
    if best_idx >= 0:
        if best_idx + 1 < len(subdiv_times):
            subdiv_dur = subdiv_times[best_idx + 1] - subdiv_times[best_idx]
        else:
            subdiv_dur = cycle_end - subdiv_times[best_idx]
        if subdiv_dur > 0 and best_dist / subdiv_dur > SNAP_TOLERANCE:
            return -1

    return best_idx


def _has_energy_at_onset(
    bp_signal: np.ndarray,
    sr: int,
    onset_time: float,
    this_freq_band: str,
    stem_name: str,
    bandpass_cache: dict[tuple[str, str], np.ndarray],
    stem_templates: dict[str, list[InstrumentTemplate]],
) -> bool:
    """Check if a bandpass-filtered signal has enough energy at an onset time.

    Compares this band's RMS to the total RMS across all distinct bands for the
    same stem in a short window around the onset.
    """
    half_win = int(ONSET_WINDOW_SEC * sr / 2)
    center = int(onset_time * sr)
    start = max(0, center - half_win)
    end = min(len(bp_signal), center + half_win)

    if end <= start:
        return False

    this_rms = np.sqrt(np.mean(bp_signal[start:end] ** 2))
    if this_rms < PRESENCE_THRESHOLD:
        return False

    # Compare to other distinct bands in the same stem
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


def _load_stems(stems_dir: str) -> dict[str, tuple[np.ndarray, int]]:
    """Load all available stem audio files."""
    stems = {}
    stems_path = Path(stems_dir)
    for stem_name in ["drums", "bass", "vocals", "other"]:
        stem_file = stems_path / f"{stem_name}.wav"
        if stem_file.exists():
            try:
                y, sr = librosa.load(str(stem_file), sr=22050, mono=True)
                stems[stem_name] = (y, sr)
            except Exception as e:
                logger.warning(f"Failed to load stem {stem_name}: {e}")
    return stems


def _bandpass_filter(
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


def _empty_result(
    genre: str,
    templates: list[InstrumentTemplate],
    cycles: list[tuple[float, float]],
) -> dict:
    """Fallback: return empty grid when stems are unavailable."""
    instrument_names = [t.name for t in templates]

    bars = []
    num_cycles = max(len(cycles), 1)
    for cycle_num in range(num_cycles):
        bars.append({
            "bar_num": cycle_num,
            "instruments": [],
        })

    return {
        "genre": genre,
        "instrument_list": instrument_names,
        "subdivisions": NUM_SUBDIVISIONS,
        "bars": bars,
    }

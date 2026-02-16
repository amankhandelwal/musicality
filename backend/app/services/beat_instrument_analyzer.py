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
ONSET_WINDOW_SEC = 0.050  # 50ms window for sub-stem energy attribution
ENERGY_RATIO_THRESHOLD = 0.4  # min energy ratio to attribute onset to sub-stem
PRESENCE_THRESHOLD = 0.005  # below this, stem has negligible energy
SNAP_TOLERANCE = 0.4  # max fraction of subdivision duration to snap
SPECTRAL_WINDOW_SEC = 0.050  # 50ms window for spectral centroid computation

# Grid regularization: blend local beat-derived positions with expected uniform grid
GRID_REGULARIZATION_ALPHA = 0.6  # weight for local beats (1-alpha for expected)

# Pattern smoothing constants
SMOOTH_WINDOW_MIN_SECTION = 3  # min bars in a section for smoothing
SECTION_BREAK_THRESHOLD = 0.3  # Jaccard similarity below this = section boundary
DEVIATION_THRESHOLD = 4  # max Hamming distance before replacing with consensus


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

    # Precompute onset times and envelopes for each stem (whole song, once)
    # Detecting on the full envelope gives librosa proper adaptive thresholding
    stem_onset_times: dict[str, np.ndarray] = {}
    stem_onset_envelopes: dict[str, np.ndarray] = {}
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
        stem_onset_envelopes[stem_name] = env
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

    # Compute global median beat period for grid regularization
    median_beat_period = None
    if len(beat_times) >= 2:
        beat_diffs = [beat_times[i + 1] - beat_times[i] for i in range(len(beat_times) - 1)]
        median_beat_period = float(np.median(beat_diffs))

    result_bars = []
    for cycle_num, (cycle_start, cycle_end) in enumerate(cycles):
        subdiv_times = _build_subdivision_grid(
            cycle_start, cycle_end, beat_times, median_beat_period
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
            stem_onset_envelopes,
            bandpass_cache,
            hop,
        )

        result_bars.append({
            "bar_num": cycle_num,
            "instruments": cycle_instruments,
        })

    result_bars = _smooth_instrument_patterns(result_bars)

    return {
        "genre": genre,
        "instrument_list": instrument_names,
        "subdivisions": NUM_SUBDIVISIONS,
        "bars": result_bars,
    }


def _smooth_instrument_patterns(result_bars: list[dict]) -> list[dict]:
    """Smooth instrument patterns across bars to enforce cross-bar consistency.

    Groups bars into sections by Jaccard similarity, then applies majority-vote
    consensus within each section. Bars that deviate too much from consensus
    are replaced. Section boundaries are preserved so real musical changes
    (e.g., derecho to mambo) are not smoothed over.
    """
    if len(result_bars) < SMOOTH_WINDOW_MIN_SECTION:
        return result_bars

    # Collect all instrument names across all bars
    all_instruments: set[str] = set()
    for bar in result_bars:
        for inst in bar["instruments"]:
            all_instruments.add(inst["instrument"])

    for inst_name in all_instruments:
        # Extract boolean patterns for this instrument across bars
        patterns: list[list[bool] | None] = []
        for bar in result_bars:
            inst_data = next(
                (i for i in bar["instruments"] if i["instrument"] == inst_name),
                None,
            )
            if inst_data is None:
                patterns.append(None)
            else:
                patterns.append([
                    cell["active"] if isinstance(cell, dict) else cell
                    for cell in inst_data["beats"]
                ])

        # Segment into sections based on Jaccard similarity
        sections = _segment_into_sections(patterns, SECTION_BREAK_THRESHOLD)

        for section_indices in sections:
            if len(section_indices) < SMOOTH_WINDOW_MIN_SECTION:
                continue

            section_patterns = [patterns[i] for i in section_indices if patterns[i] is not None]
            if len(section_patterns) < SMOOTH_WINDOW_MIN_SECTION:
                continue

            consensus = _compute_consensus(section_patterns)

            for bar_idx in section_indices:
                if patterns[bar_idx] is None:
                    continue

                hamming = sum(
                    a != b for a, b in zip(patterns[bar_idx], consensus)
                )
                if hamming > DEVIATION_THRESHOLD:
                    _apply_consensus(
                        result_bars, bar_idx, inst_name, consensus,
                        section_indices,
                    )

    return result_bars


def _segment_into_sections(
    patterns: list[list[bool] | None],
    threshold: float,
) -> list[list[int]]:
    """Group bar indices into sections based on Jaccard similarity of consecutive bars."""
    sections: list[list[int]] = []
    current_section: list[int] = [0]

    for i in range(1, len(patterns)):
        prev = patterns[i - 1]
        curr = patterns[i]

        if prev is None or curr is None:
            # None patterns break sections
            if current_section:
                sections.append(current_section)
            current_section = [i]
            continue

        jaccard = _jaccard_similarity(prev, curr)
        if jaccard < threshold:
            sections.append(current_section)
            current_section = [i]
        else:
            current_section.append(i)

    if current_section:
        sections.append(current_section)

    return sections


def _jaccard_similarity(a: list[bool], b: list[bool]) -> float:
    """Compute Jaccard similarity between two boolean patterns."""
    set_a = {i for i, v in enumerate(a) if v}
    set_b = {i for i, v in enumerate(b) if v}

    if not set_a and not set_b:
        return 1.0  # both empty = identical

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _compute_consensus(section_patterns: list[list[bool]]) -> list[bool]:
    """Compute majority-vote consensus pattern from a list of boolean patterns."""
    n = len(section_patterns)
    consensus = []
    for subdiv in range(NUM_SUBDIVISIONS):
        active_count = sum(1 for p in section_patterns if p[subdiv])
        consensus.append(active_count >= n / 2)
    return consensus


def _apply_consensus(
    result_bars: list[dict],
    bar_idx: int,
    inst_name: str,
    consensus: list[bool],
    section_indices: list[int],
) -> None:
    """Replace a noisy bar's pattern with the consensus, averaging velocity/pitch from neighbors."""
    bar = result_bars[bar_idx]
    inst_data = next(
        (i for i in bar["instruments"] if i["instrument"] == inst_name),
        None,
    )
    if inst_data is None:
        return

    # Find nearest non-replaced bars in the section for velocity/pitch averaging
    neighbor_velocities: list[list[float]] = [[] for _ in range(NUM_SUBDIVISIONS)]
    neighbor_pitches: list[list[float]] = [[] for _ in range(NUM_SUBDIVISIONS)]

    for idx in section_indices:
        if idx == bar_idx:
            continue
        other_bar = result_bars[idx]
        other_inst = next(
            (i for i in other_bar["instruments"] if i["instrument"] == inst_name),
            None,
        )
        if other_inst is None:
            continue
        for s in range(NUM_SUBDIVISIONS):
            cell = other_inst["beats"][s]
            if isinstance(cell, dict) and cell.get("active"):
                neighbor_velocities[s].append(cell.get("velocity", 0.7))
                neighbor_pitches[s].append(cell.get("pitch", 0.5))

    # Apply consensus pattern
    for s in range(NUM_SUBDIVISIONS):
        if consensus[s]:
            avg_vel = (
                sum(neighbor_velocities[s]) / len(neighbor_velocities[s])
                if neighbor_velocities[s]
                else 0.7
            )
            avg_pitch = (
                sum(neighbor_pitches[s]) / len(neighbor_pitches[s])
                if neighbor_pitches[s]
                else 0.5
            )
            inst_data["beats"][s] = {
                "active": True,
                "velocity": round(avg_vel, 3),
                "pitch": round(avg_pitch, 3),
            }
        else:
            inst_data["beats"][s] = {
                "active": False,
                "velocity": 0.0,
                "pitch": 0.5,
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
    median_beat_period: float | None = None,
) -> list[float]:
    """Build 16 subdivision timestamps for an 8-count cycle.

    Uses actual beat times within the cycle, blended with an expected uniform
    grid derived from the global median beat period. This dampens 10-20ms
    timing jitter while preserving real tempo changes.

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

    # Blend local subdivisions with expected uniform grid to reduce jitter
    if median_beat_period is not None:
        expected = _build_expected_grid(cycle_start, median_beat_period)
        alpha = GRID_REGULARIZATION_ALPHA
        subdivs = [
            alpha * local + (1 - alpha) * exp
            for local, exp in zip(subdivs, expected)
        ]

    return subdivs


def _build_expected_grid(
    cycle_start: float,
    median_beat_period: float,
) -> list[float]:
    """Build an expected uniform 16-subdivision grid from median beat period.

    8 beats spaced by median_beat_period, with "&" midpoints between each.
    """
    expected = []
    for i in range(8):
        beat_time = cycle_start + i * median_beat_period
        expected.append(beat_time)  # on-beat
        expected.append(beat_time + median_beat_period / 2.0)  # "&"
    return expected[:NUM_SUBDIVISIONS]


def _analyze_cycle_onsets(
    cycle_num: int,
    cycle_start: float,
    cycle_end: float,
    subdiv_times: list[float],
    templates: list[InstrumentTemplate],
    stem_templates: dict[str, list[InstrumentTemplate]],
    stems_audio: dict[str, tuple[np.ndarray, int]],
    stem_onset_times: dict[str, np.ndarray],
    stem_onset_envelopes: dict[str, np.ndarray],
    bandpass_cache: dict[tuple[str, str], np.ndarray],
    hop: int,
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

        pattern = [{"active": False, "velocity": 0.0, "pitch": 0.5}
                    for _ in range(NUM_SUBDIVISIONS)]
        y, sr = stems_audio[template.stem]
        onset_env = stem_onset_envelopes.get(template.stem)

        for onset_time in onsets:
            subdiv_idx = _snap_to_subdivision(onset_time, subdiv_times, cycle_end)
            if subdiv_idx < 0 or subdiv_idx >= NUM_SUBDIVISIONS:
                continue

            activated = False
            if is_single_band:
                activated = True
            else:
                bp_key = (template.stem, template.freq_band)
                bp_signal = bandpass_cache.get(bp_key)
                if bp_signal is None:
                    continue

                if _has_energy_at_onset(
                    bp_signal, sr, onset_time, template.freq_band,
                    template.stem, bandpass_cache, stem_templates,
                ):
                    activated = True

            if activated:
                velocity = _compute_onset_velocity(onset_time, onset_env, sr, hop)
                bp_key = (template.stem, template.freq_band)
                bp_signal = bandpass_cache.get(bp_key)
                pitch = _compute_spectral_pitch(
                    bp_signal, sr, onset_time, template.freq_band
                ) if bp_signal is not None else 0.5
                pattern[subdiv_idx] = {
                    "active": True,
                    "velocity": velocity,
                    "pitch": pitch,
                }

        if any(cell["active"] for cell in pattern):
            active_velocities = [cell["velocity"] for cell in pattern if cell["active"]]
            confidence = sum(active_velocities) / len(active_velocities) if active_velocities else 0.7
            instruments.append({
                "instrument": template.name,
                "beats": pattern,
                "confidence": round(confidence, 3),
            })

    if cycle_num == 0:
        logger.info(
            "Cycle 0: %d onsets across stems %s → %d instruments",
            sum(len(v) for v in cycle_onsets.values()),
            {k: len(v) for k, v in cycle_onsets.items()},
            len(instruments),
        )

    return instruments


def _compute_onset_velocity(
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
    # Power compression to avoid extremes
    compressed = float(np.power(normalized, 0.7))
    return round(max(0.0, min(1.0, compressed)), 3)


def _compute_spectral_pitch(
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

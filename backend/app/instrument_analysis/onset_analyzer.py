"""Onset-based instrument analyzer composing signal processing, grid, and smoothing."""

from __future__ import annotations

import logging

import librosa
import numpy as np

from app.genre.models import FREQ_BANDS, InstrumentTemplate
from app.instrument_analysis.pattern_smoother import PatternSmoother
from app.instrument_analysis.signal_processing import (
    bandpass_filter,
    compute_onset_velocity,
    compute_spectral_pitch,
    has_energy_at_onset,
    load_stems,
    snap_to_subdivision,
)
from app.instrument_analysis.subdivision_grid import NUM_SUBDIVISIONS, SubdivisionGridBuilder

logger = logging.getLogger(__name__)


class OnsetInstrumentAnalyzer:
    def __init__(
        self,
        template_provider: object,
        grid_builder: SubdivisionGridBuilder | None = None,
        smoother: PatternSmoother | None = None,
    ) -> None:
        self._template_provider = template_provider
        self._grid_builder = grid_builder or SubdivisionGridBuilder()
        self._smoother = smoother or PatternSmoother()

    def analyze(
        self,
        genre: str,
        bars: list[dict],
        beats: list[dict],
        stems_dir: str | None,
        tempo: float,
    ) -> dict:
        """Analyze instruments beat-by-beat across all 8-count cycles."""
        templates = self._template_provider.get_templates(genre)
        instrument_names = [t.name for t in templates]

        cycles = self._grid_builder.pair_bars_into_cycles(bars)

        if not cycles or not stems_dir:
            return self._empty_result(genre, templates, cycles)

        stems_audio = load_stems(stems_dir)
        if not stems_audio:
            return self._empty_result(genre, templates, cycles)

        # Precompute onset times and envelopes for each stem
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

        # Precompute bandpass-filtered stems
        bandpass_cache: dict[tuple[str, str], np.ndarray] = {}
        for t in templates:
            key = (t.stem, t.freq_band)
            if key not in bandpass_cache and t.stem in stems_audio:
                y, sr = stems_audio[t.stem]
                freq_low, freq_high = FREQ_BANDS[t.freq_band]
                bandpass_cache[key] = bandpass_filter(y, sr, freq_low, freq_high)

        # Group templates by stem
        stem_templates: dict[str, list[InstrumentTemplate]] = {}
        for t in templates:
            stem_templates.setdefault(t.stem, []).append(t)

        beat_times = [b["time"] for b in beats]

        # Compute global median beat period
        median_beat_period = None
        if len(beat_times) >= 2:
            beat_diffs = [beat_times[i + 1] - beat_times[i] for i in range(len(beat_times) - 1)]
            median_beat_period = float(np.median(beat_diffs))

        result_bars = []
        for cycle_num, (cycle_start, cycle_end) in enumerate(cycles):
            subdiv_times = self._grid_builder.build_grid(
                cycle_start, cycle_end, beat_times, median_beat_period
            )

            cycle_instruments = self._analyze_cycle_onsets(
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

        result_bars = self._smoother.smooth(result_bars)

        return {
            "genre": genre,
            "instrument_list": instrument_names,
            "subdivisions": NUM_SUBDIVISIONS,
            "bars": result_bars,
        }

    def _analyze_cycle_onsets(
        self,
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
        cycle_onsets: dict[str, list[float]] = {}
        for stem_name, all_onsets in stem_onset_times.items():
            mask = (all_onsets >= cycle_start) & (all_onsets < cycle_end)
            cycle_onsets[stem_name] = list(all_onsets[mask])

        instruments = []
        for template in templates:
            if template.stem not in stems_audio:
                continue

            onsets = cycle_onsets.get(template.stem, [])
            stem_bands = {t.freq_band for t in stem_templates.get(template.stem, [])}
            is_single_band = len(stem_bands) <= 1

            pattern = [{"active": False, "velocity": 0.0, "pitch": 0.5}
                        for _ in range(NUM_SUBDIVISIONS)]
            y, sr = stems_audio[template.stem]
            onset_env = stem_onset_envelopes.get(template.stem)

            for onset_time in onsets:
                subdiv_idx = snap_to_subdivision(onset_time, subdiv_times, cycle_end)
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

                    if has_energy_at_onset(
                        bp_signal, sr, onset_time, template.freq_band,
                        template.stem, bandpass_cache, stem_templates,
                    ):
                        activated = True

                if activated:
                    velocity = compute_onset_velocity(onset_time, onset_env, sr, hop)
                    bp_key = (template.stem, template.freq_band)
                    bp_signal = bandpass_cache.get(bp_key)
                    pitch = compute_spectral_pitch(
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

    def _empty_result(
        self,
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

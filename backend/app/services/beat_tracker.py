from __future__ import annotations

import numpy as np


def detect_beats(audio_path: str) -> tuple[list[dict], list[dict], float]:
    """Detect beats and downbeats using madmom.

    Returns (beats, bars, tempo) where:
    - beats: list of {"time": float, "beat_num": int}
    - bars: list of {"start": float, "end": float, "bar_num": int}
    - tempo: float BPM
    """
    from madmom.features.beats import DBNBeatTrackingProcessor, RNNBeatProcessor
    from madmom.features.downbeats import (
        DBNDownBeatTrackingProcessor,
        RNNDownBeatProcessor,
    )

    # Beat detection
    beat_proc = RNNBeatProcessor()(audio_path)
    beat_tracker = DBNBeatTrackingProcessor(fps=100)
    beat_times = beat_tracker(beat_proc)

    # Downbeat detection
    try:
        downbeat_proc = RNNDownBeatProcessor()(audio_path)
        downbeat_tracker = DBNDownBeatTrackingProcessor(beats_per_bar=[4], fps=100)
        downbeat_result = downbeat_tracker(downbeat_proc)
        # downbeat_result is Nx2 array: [time, beat_position]
        downbeat_times = downbeat_result[:, 0]
        beat_positions = downbeat_result[:, 1].astype(int)
    except Exception:
        # Fallback: assign beat numbers cycling 1-4
        downbeat_times = beat_times
        beat_positions = np.array([(i % 4) + 1 for i in range(len(beat_times))])

    # Calculate tempo from median inter-beat interval
    if len(beat_times) >= 2:
        ibis = np.diff(beat_times)
        median_ibi = float(np.median(ibis))
        tempo = 60.0 / median_ibi if median_ibi > 0 else 120.0
    else:
        tempo = 120.0

    # Build beat list with 8-count (two bars of 4)
    beats = []
    for t, pos in zip(downbeat_times, beat_positions):
        beats.append({"time": float(t), "beat_num": int(pos)})

    # Extend to 8-count: beats 5-8 are the second bar of 4
    eight_count_beats = []
    bar_cycle = 0
    for b in beats:
        num = b["beat_num"]
        if num == 1:
            bar_cycle += 1
        adjusted = num if (bar_cycle % 2 == 1) else num + 4
        eight_count_beats.append({"time": b["time"], "beat_num": adjusted})

    # Build bars
    bars = []
    bar_start = None
    bar_num = 0
    for i, b in enumerate(beats):
        if b["beat_num"] == 1:
            if bar_start is not None:
                bars.append({"start": bar_start, "end": b["time"], "bar_num": bar_num})
            bar_num += 1
            bar_start = b["time"]
    # Close last bar
    if bar_start is not None and len(beats) > 0:
        bars.append({"start": bar_start, "end": beats[-1]["time"], "bar_num": bar_num})

    return eight_count_beats, bars, tempo

from __future__ import annotations

import numpy as np

from app.beat_detection.models import BarInfo, BeatDetectionResult, BeatInfo


class MadmomBeatDetector:
    def detect(self, audio_path: str) -> BeatDetectionResult:
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
            downbeat_times = downbeat_result[:, 0]
            beat_positions = downbeat_result[:, 1].astype(int)
        except Exception:
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
        beats_raw = []
        for t, pos in zip(downbeat_times, beat_positions):
            beats_raw.append({"time": float(t), "beat_num": int(pos)})

        # Extend to 8-count: beats 5-8 are the second bar of 4
        eight_count_beats = []
        bar_cycle = 0
        for b in beats_raw:
            num = b["beat_num"]
            if num == 1:
                bar_cycle += 1
            adjusted = num if (bar_cycle % 2 == 1) else num + 4
            eight_count_beats.append({"time": b["time"], "beat_num": adjusted})

        # Build bars
        bars_raw: list[dict] = []
        bar_start = None
        bar_num = 0
        for b in beats_raw:
            if b["beat_num"] == 1:
                if bar_start is not None:
                    bars_raw.append({"start": bar_start, "end": b["time"], "bar_num": bar_num})
                bar_num += 1
                bar_start = b["time"]
        if bar_start is not None and len(beats_raw) > 0:
            bars_raw.append({"start": bar_start, "end": beats_raw[-1]["time"], "bar_num": bar_num})

        beats = [BeatInfo(time=b["time"], beat_num=b["beat_num"]) for b in eight_count_beats]
        bars = [BarInfo(start=b["start"], end=b["end"], bar_num=b["bar_num"]) for b in bars_raw]

        return BeatDetectionResult(beats=beats, bars=bars, tempo=tempo)

"""Subdivision grid construction for beat cycles."""

from __future__ import annotations

NUM_SUBDIVISIONS = 16
GRID_REGULARIZATION_ALPHA = 0.6


class SubdivisionGridBuilder:
    def pair_bars_into_cycles(self, bars: list[dict]) -> list[tuple[float, float]]:
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

    def build_grid(
        self,
        cycle_start: float,
        cycle_end: float,
        beat_times: list[float],
        median_beat_period: float | None = None,
    ) -> list[float]:
        """Build 16 subdivision timestamps for an 8-count cycle."""
        cycle_beats = [t for t in beat_times if cycle_start <= t < cycle_end]

        if len(cycle_beats) < 2:
            step = (cycle_end - cycle_start) / NUM_SUBDIVISIONS
            return [cycle_start + i * step for i in range(NUM_SUBDIVISIONS)]

        subdivs = []
        for i, bt in enumerate(cycle_beats):
            subdivs.append(bt)
            if i + 1 < len(cycle_beats):
                subdivs.append((bt + cycle_beats[i + 1]) / 2.0)
            else:
                if i > 0:
                    gap = bt - cycle_beats[i - 1]
                else:
                    gap = (cycle_end - cycle_start) / 8.0
                subdivs.append(bt + gap / 2.0)

        if len(subdivs) < NUM_SUBDIVISIONS:
            last = subdivs[-1]
            remaining = NUM_SUBDIVISIONS - len(subdivs)
            gap = (cycle_end - last) / (remaining + 1)
            for j in range(1, remaining + 1):
                subdivs.append(last + j * gap)
        subdivs = subdivs[:NUM_SUBDIVISIONS]

        if median_beat_period is not None:
            expected = self.build_expected_grid(cycle_start, median_beat_period)
            alpha = GRID_REGULARIZATION_ALPHA
            subdivs = [
                alpha * local + (1 - alpha) * exp
                for local, exp in zip(subdivs, expected)
            ]

        return subdivs

    def build_expected_grid(
        self,
        cycle_start: float,
        median_beat_period: float,
    ) -> list[float]:
        """Build an expected uniform 16-subdivision grid from median beat period."""
        expected = []
        for i in range(8):
            beat_time = cycle_start + i * median_beat_period
            expected.append(beat_time)
            expected.append(beat_time + median_beat_period / 2.0)
        return expected[:NUM_SUBDIVISIONS]

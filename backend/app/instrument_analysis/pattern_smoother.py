"""Pattern smoothing via Jaccard similarity and majority-vote consensus."""

from __future__ import annotations

from app.instrument_analysis.subdivision_grid import NUM_SUBDIVISIONS

SMOOTH_WINDOW_MIN_SECTION = 3
SECTION_BREAK_THRESHOLD = 0.3
DEVIATION_THRESHOLD = 4


class PatternSmoother:
    def smooth(self, result_bars: list[dict]) -> list[dict]:
        """Smooth instrument patterns across bars to enforce cross-bar consistency."""
        if len(result_bars) < SMOOTH_WINDOW_MIN_SECTION:
            return result_bars

        all_instruments: set[str] = set()
        for bar in result_bars:
            for inst in bar["instruments"]:
                all_instruments.add(inst["instrument"])

        for inst_name in all_instruments:
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

            sections = self.segment_into_sections(patterns, SECTION_BREAK_THRESHOLD)

            for section_indices in sections:
                if len(section_indices) < SMOOTH_WINDOW_MIN_SECTION:
                    continue

                section_patterns = [patterns[i] for i in section_indices if patterns[i] is not None]
                if len(section_patterns) < SMOOTH_WINDOW_MIN_SECTION:
                    continue

                consensus = self.compute_consensus(section_patterns)

                for bar_idx in section_indices:
                    if patterns[bar_idx] is None:
                        continue

                    hamming = sum(
                        a != b for a, b in zip(patterns[bar_idx], consensus)
                    )
                    if hamming > DEVIATION_THRESHOLD:
                        self._apply_consensus(
                            result_bars, bar_idx, inst_name, consensus,
                            section_indices,
                        )

        return result_bars

    def segment_into_sections(
        self,
        patterns: list[list[bool] | None],
        threshold: float,
    ) -> list[list[int]]:
        """Group bar indices into sections based on Jaccard similarity."""
        sections: list[list[int]] = []
        current_section: list[int] = [0]

        for i in range(1, len(patterns)):
            prev = patterns[i - 1]
            curr = patterns[i]

            if prev is None or curr is None:
                if current_section:
                    sections.append(current_section)
                current_section = [i]
                continue

            jaccard = self.jaccard_similarity(prev, curr)
            if jaccard < threshold:
                sections.append(current_section)
                current_section = [i]
            else:
                current_section.append(i)

        if current_section:
            sections.append(current_section)

        return sections

    def jaccard_similarity(self, a: list[bool], b: list[bool]) -> float:
        """Compute Jaccard similarity between two boolean patterns."""
        set_a = {i for i, v in enumerate(a) if v}
        set_b = {i for i, v in enumerate(b) if v}

        if not set_a and not set_b:
            return 1.0

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def compute_consensus(self, section_patterns: list[list[bool]]) -> list[bool]:
        """Compute majority-vote consensus pattern."""
        n = len(section_patterns)
        consensus = []
        for subdiv in range(NUM_SUBDIVISIONS):
            active_count = sum(1 for p in section_patterns if p[subdiv])
            consensus.append(active_count >= n / 2)
        return consensus

    def _apply_consensus(
        self,
        result_bars: list[dict],
        bar_idx: int,
        inst_name: str,
        consensus: list[bool],
        section_indices: list[int],
    ) -> None:
        """Replace a noisy bar's pattern with the consensus."""
        bar = result_bars[bar_idx]
        inst_data = next(
            (i for i in bar["instruments"] if i["instrument"] == inst_name),
            None,
        )
        if inst_data is None:
            return

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

import type { Section } from "../types/analysis";
import "./SectionTimeline.css";

interface SectionTimelineProps {
  sections: Section[];
  duration: number;
  currentTime: number;
  onSeek: (time: number) => void;
}

const SECTION_COLORS: Record<string, string> = {
  derecho: "#4a9eff",
  majao: "#ff6b6b",
  mambo: "#ffd93d",
  tema: "#4a9eff",
  montuno: "#ff6b6b",
};

export function SectionTimeline({
  sections,
  duration,
  currentTime,
  onSeek,
}: SectionTimelineProps) {
  if (duration <= 0) return null;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    onSeek(pct * duration);
  };

  const playheadPct = (currentTime / duration) * 100;

  return (
    <div className="section-timeline" onClick={handleClick}>
      <div className="section-timeline__bar">
        {sections.map((s, i) => {
          const left = (s.start / duration) * 100;
          const width = ((s.end - s.start) / duration) * 100;
          const color = SECTION_COLORS[s.latin_label] || "#555";
          return (
            <div
              key={i}
              className="section-timeline__segment"
              style={{ left: `${left}%`, width: `${width}%`, backgroundColor: color }}
              title={`${s.latin_label} (${s.label})`}
            >
              <span className="section-timeline__segment-label">{s.latin_label}</span>
            </div>
          );
        })}
        <div
          className="section-timeline__playhead"
          style={{ left: `${playheadPct}%` }}
        />
      </div>
    </div>
  );
}

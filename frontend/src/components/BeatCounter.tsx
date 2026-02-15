import "./BeatCounter.css";

interface BeatCounterProps {
  currentBeatNum: number;
  latinLabel: string | null;
}

const SECTION_COLORS: Record<string, string> = {
  derecho: "#4a9eff",
  majao: "#ff6b6b",
  mambo: "#ffd93d",
  tema: "#4a9eff",
  montuno: "#ff6b6b",
};

export function BeatCounter({ currentBeatNum, latinLabel }: BeatCounterProps) {
  const color = latinLabel ? SECTION_COLORS[latinLabel] || "#888" : "#888";

  return (
    <div className="beat-counter">
      <div className="beat-counter__label">
        {latinLabel && (
          <span className="beat-counter__section" style={{ color }}>
            {latinLabel.toUpperCase()}
          </span>
        )}
      </div>
      <div className="beat-counter__beats">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
          <div
            key={num}
            className={`beat-counter__beat ${
              currentBeatNum === num ? "beat-counter__beat--active" : ""
            }`}
            style={
              currentBeatNum === num ? { backgroundColor: color, borderColor: color } : undefined
            }
          >
            {num}
          </div>
        ))}
      </div>
    </div>
  );
}

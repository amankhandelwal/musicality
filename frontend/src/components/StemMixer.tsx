import type { StemName } from "../hooks/useStemPlayer";
import "./StemMixer.css";

interface StemMixerProps {
  mutedStems: Set<StemName>;
  soloedStem: StemName | null;
  onToggleMute: (stem: StemName) => void;
  onSolo: (stem: StemName | null) => void;
}

const STEM_CONFIG: { name: StemName; label: string; color: string }[] = [
  { name: "drums", label: "Drums", color: "#f59e0b" },
  { name: "bass", label: "Bass", color: "#3b82f6" },
  { name: "vocals", label: "Vocals", color: "#ec4899" },
  { name: "other", label: "Other", color: "#a855f7" },
];

export function StemMixer({
  mutedStems,
  soloedStem,
  onToggleMute,
  onSolo,
}: StemMixerProps) {
  return (
    <div className="stem-mixer">
      {STEM_CONFIG.map(({ name, label, color }) => {
        const isMuted =
          mutedStems.has(name) || (soloedStem !== null && soloedStem !== name);

        return (
          <div
            key={name}
            className={`stem-mixer__stem${isMuted ? " stem-mixer__stem--muted" : ""}`}
          >
            <div
              className="stem-mixer__color-dot"
              style={{ background: color }}
            />
            <span className="stem-mixer__label">{label}</span>
            <button
              className={`stem-mixer__btn${mutedStems.has(name) ? " stem-mixer__btn--mute-active" : ""}`}
              onClick={() => onToggleMute(name)}
              title={mutedStems.has(name) ? "Unmute" : "Mute"}
            >
              {mutedStems.has(name) ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 5L6 9H2v6h4l5 4V5z" />
                  <line x1="23" y1="9" x2="17" y2="15" />
                  <line x1="17" y1="9" x2="23" y2="15" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 5L6 9H2v6h4l5 4V5z" />
                  <path d="M19.07 4.93a10 10 0 010 14.14" />
                  <path d="M15.54 8.46a5 5 0 010 7.07" />
                </svg>
              )}
            </button>
            <button
              className={`stem-mixer__btn${soloedStem === name ? " stem-mixer__btn--solo-active" : ""}`}
              onClick={() => onSolo(name)}
              title={soloedStem === name ? "Unsolo" : "Solo"}
            >
              S
            </button>
          </div>
        );
      })}
    </div>
  );
}

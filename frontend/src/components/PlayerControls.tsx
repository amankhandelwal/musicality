import "./PlayerControls.css";

interface PlayerControlsProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onToggle: () => void;
  onSeek: (time: number) => void;
  onSkipForward: () => void;
  onSkipBackward: () => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function PlayerControls({
  isPlaying,
  currentTime,
  duration,
  onToggle,
  onSeek,
  onSkipForward,
  onSkipBackward,
}: PlayerControlsProps) {
  const handleSeekBar = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSeek(Number(e.target.value));
  };

  return (
    <div className="player-controls">
      <div className="player-controls__buttons">
        <button className="player-controls__btn" onClick={onSkipBackward} title="Back 10s">
          -10s
        </button>
        <button className="player-controls__btn player-controls__btn--play" onClick={onToggle}>
          {isPlaying ? "Pause" : "Play"}
        </button>
        <button className="player-controls__btn" onClick={onSkipForward} title="Forward 10s">
          +10s
        </button>
      </div>
      <div className="player-controls__seek">
        <span className="player-controls__time">{formatTime(currentTime)}</span>
        <input
          type="range"
          className="player-controls__slider"
          min={0}
          max={duration || 0}
          step={0.1}
          value={currentTime}
          onChange={handleSeekBar}
        />
        <span className="player-controls__time">{formatTime(duration)}</span>
      </div>
    </div>
  );
}

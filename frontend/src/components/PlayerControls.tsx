import { useRef, useCallback, useState } from "react";
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
  const trackRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const seekFromEvent = useCallback(
    (e: React.MouseEvent | MouseEvent) => {
      if (!trackRef.current || duration <= 0) return;
      const rect = trackRef.current.getBoundingClientRect();
      const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      onSeek(pct * duration);
    },
    [duration, onSeek]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      setIsDragging(true);
      seekFromEvent(e);

      const onMouseMove = (ev: MouseEvent) => seekFromEvent(ev);
      const onMouseUp = () => {
        setIsDragging(false);
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
      };
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    },
    [seekFromEvent]
  );

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="player-controls">
      {/* Seek bar on top */}
      <div className="player-controls__seek">
        <span className="player-controls__time">{formatTime(currentTime)}</span>
        <div
          className={`player-controls__track ${isDragging ? "player-controls__track--dragging" : ""}`}
          ref={trackRef}
          onMouseDown={handleMouseDown}
        >
          <div
            className="player-controls__track-fill"
            style={{ width: `${progress}%` }}
          />
          <div
            className="player-controls__thumb"
            style={{ left: `${progress}%` }}
          />
        </div>
        <span className="player-controls__time">{formatTime(duration)}</span>
      </div>

      {/* Controls below */}
      <div className="player-controls__buttons">
        <button className="player-controls__btn" onClick={onSkipBackward} title="Back 10s">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 19l-7-7 7-7" />
            <path d="M18 19l-7-7 7-7" />
          </svg>
        </button>
        <button className="player-controls__btn player-controls__btn--play" onClick={onToggle}>
          {isPlaying ? (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
        <button className="player-controls__btn" onClick={onSkipForward} title="Forward 10s">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 5l7 7-7 7" />
            <path d="M6 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

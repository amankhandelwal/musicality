import { useState, useEffect } from "react";
import { useAnalysis } from "./hooks/useAnalysis";
import { useAudioPlayer } from "./hooks/useAudioPlayer";
import { useBeatSync } from "./hooks/useBeatSync";
import { PlayerControls } from "./components/PlayerControls";
import { InstrumentGrid } from "./components/InstrumentGrid";
import "./styles/globals.css";

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued...",
  downloading: "Downloading audio...",
  detecting_beats: "Detecting beats...",
  separating_stems: "Separating instruments...",
  analyzing_instruments: "Analyzing instruments...",
};

function App() {
  const [url, setUrl] = useState("");
  const analysis = useAnalysis();
  const player = useAudioPlayer();

  const beats = analysis.result?.beats ?? [];
  const bars = analysis.result?.bars ?? [];
  const {
    currentBeatNum,
    currentBarNum,
    currentSubdivision,
  } = useBeatSync(beats, bars, player.currentTime);

  useEffect(() => {
    if (analysis.audioUrl && analysis.result) {
      player.load(analysis.audioUrl);
    }
  }, [analysis.audioUrl, analysis.result]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      analysis.submit(url.trim());
    }
  };

  return (
    <div className="app">
      <div className="top-bar">
        <span className="top-bar__title">Musicality</span>
        <form className="url-form" onSubmit={handleSubmit}>
          <input
            className="url-form__input"
            type="text"
            placeholder="Paste a YouTube URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={analysis.isLoading}
          />
          <button
            className="url-form__btn"
            type="submit"
            disabled={analysis.isLoading || !url.trim()}
          >
            {analysis.isLoading ? "Analyzing..." : "Analyze"}
          </button>
        </form>
      </div>

      {analysis.isLoading && analysis.status && (
        <div className="processing-status">
          <div className="processing-status__text">
            {STATUS_LABELS[analysis.status] || analysis.status}
          </div>
          <div className="processing-status__bar">
            <div
              className="processing-status__fill"
              style={{ width: `${analysis.progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {analysis.error && (
        <div className="error-message">{analysis.error}</div>
      )}

      {analysis.result && (
        <>
          <div className="song-info">
            <span className="song-info__title">{analysis.result.metadata.title}</span>
            <span className="song-info__meta">
              {Math.round(analysis.result.tempo)} BPM &middot;{" "}
              {analysis.result.metadata.genre_hint}
            </span>
          </div>

          <PlayerControls
            isPlaying={player.isPlaying}
            currentTime={player.currentTime}
            duration={player.duration}
            onToggle={player.toggle}
            onSeek={player.seek}
            onSkipForward={player.skipForward}
            onSkipBackward={player.skipBackward}
          />

          <div className="panels">
            <InstrumentGrid
              grid={analysis.result.instrument_grid}
              currentBarNum={currentBarNum}
              currentSubdivision={currentSubdivision}
              currentBeatNum={currentBeatNum}
            />
          </div>
        </>
      )}
    </div>
  );
}

export default App;

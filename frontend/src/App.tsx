import { useState, useEffect } from "react";
import { useAnalysis } from "./hooks/useAnalysis";
import { useStemPlayer } from "./hooks/useStemPlayer";
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
  const player = useStemPlayer();

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

  const hasResult = !!analysis.result;
  const isLanding = !hasResult;

  const searchForm = (
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
  );

  return (
    <div className={`app ${hasResult ? "app--results" : ""}`}>
      {isLanding ? (
        <div className="landing">
          <h1 className="landing__title">Musicality</h1>
          <p className="landing__subtitle">
            Visualize salsa &amp; bachata music structure
          </p>
          {searchForm}

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
        </div>
      ) : (
        <>
          <div className="top-bar">
            <span className="top-bar__title">Musicality</span>
            {searchForm}
          </div>

          <div className="song-info">
            <span className="song-info__title">{analysis.result!.metadata.title}</span>
            <span className="song-info__meta">
              {Math.round(analysis.result!.tempo)} BPM &middot;{" "}
              {analysis.result!.metadata.genre_hint}
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
              grid={analysis.result!.instrument_grid}
              currentBarNum={currentBarNum}
              currentSubdivision={currentSubdivision}
              currentBeatNum={currentBeatNum}
              mutedStems={player.stemsAvailable ? player.mutedStems : undefined}
              soloedStem={player.stemsAvailable ? player.soloedStem : undefined}
              onToggleMute={player.stemsAvailable ? player.toggleMute : undefined}
              onUnmuteAll={player.stemsAvailable ? player.unmuteAll : undefined}
              onSolo={player.stemsAvailable ? player.solo : undefined}
            />
          </div>
        </>
      )}
    </div>
  );
}

export default App;

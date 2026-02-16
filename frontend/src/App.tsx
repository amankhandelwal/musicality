import { useState, useEffect } from "react";
import { useAnalysis } from "./hooks/useAnalysis";
import { useStemPlayer } from "./hooks/useStemPlayer";
import { useBeatSync } from "./hooks/useBeatSync";
import { LandingPage } from "./pages/LandingPage";
import { ResultsPage } from "./pages/ResultsPage";
import type { GenreOption } from "./types/analysis";
import "./styles/globals.css";

function App() {
  const [url, setUrl] = useState("");
  const [genre, setGenre] = useState<GenreOption>("bachata");
  const analysis = useAnalysis();
  const player = useStemPlayer();

  const beats = analysis.result?.beats ?? [];
  const bars = analysis.result?.bars ?? [];
  const { currentBeatNum, currentBarNum, currentSubdivision } = useBeatSync(
    beats,
    bars,
    player.currentTime
  );

  useEffect(() => {
    if (analysis.audioUrl && analysis.result) {
      player.load(analysis.audioUrl);
    }
  }, [analysis.audioUrl, analysis.result]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      analysis.submit(url.trim(), genre);
    }
  };

  const hasResult = !!analysis.result;

  return (
    <div className={`app ${hasResult ? "app--results" : ""}`}>
      {!hasResult ? (
        <LandingPage
          url={url}
          onUrlChange={setUrl}
          genre={genre}
          onGenreChange={setGenre}
          onSubmit={handleSubmit}
          isLoading={analysis.isLoading}
          status={analysis.status}
          progress={analysis.progress}
          error={analysis.error}
        />
      ) : (
        <ResultsPage
          result={analysis.result!}
          url={url}
          onUrlChange={setUrl}
          genre={genre}
          onGenreChange={setGenre}
          onSubmit={handleSubmit}
          isLoading={analysis.isLoading}
          isPlaying={player.isPlaying}
          currentTime={player.currentTime}
          duration={player.duration}
          onToggle={player.toggle}
          onSeek={player.seek}
          onSkipForward={player.skipForward}
          onSkipBackward={player.skipBackward}
          currentBarNum={currentBarNum}
          currentSubdivision={currentSubdivision}
          currentBeatNum={currentBeatNum}
          stemsAvailable={player.stemsAvailable}
          mutedStems={player.mutedStems}
          soloedStem={player.soloedStem}
          onToggleMute={player.toggleMute}
          onUnmuteAll={player.unmuteAll}
          onSolo={player.solo}
        />
      )}
    </div>
  );
}

export default App;

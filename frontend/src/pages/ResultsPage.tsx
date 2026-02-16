import type { AnalysisResult, GenreOption } from "../types/analysis";
import type { StemName } from "../types/audio";
import { GenreToggle } from "../components/GenreToggle";
import { InstrumentGrid } from "../components/InstrumentGrid";
import { PlayerControls } from "../components/PlayerControls";
import { SongInfo } from "../components/SongInfo";
import { UrlForm } from "../components/UrlForm";

interface ResultsPageProps {
  result: AnalysisResult;
  url: string;
  onUrlChange: (url: string) => void;
  genre: GenreOption;
  onGenreChange: (genre: GenreOption) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  // Player
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onToggle: () => void;
  onSeek: (time: number) => void;
  onSkipForward: () => void;
  onSkipBackward: () => void;
  // Beat sync
  currentBarNum: number;
  currentSubdivision: number;
  currentBeatNum: number;
  // Stems
  stemsAvailable: boolean;
  mutedStems?: Set<StemName>;
  soloedStem?: StemName | null;
  onToggleMute?: (stem: StemName) => void;
  onUnmuteAll?: () => void;
  onSolo?: (stem: StemName | null) => void;
}

export function ResultsPage({
  result,
  url,
  onUrlChange,
  genre,
  onGenreChange,
  onSubmit,
  isLoading,
  isPlaying,
  currentTime,
  duration,
  onToggle,
  onSeek,
  onSkipForward,
  onSkipBackward,
  currentBarNum,
  currentSubdivision,
  currentBeatNum,
  stemsAvailable,
  mutedStems,
  soloedStem,
  onToggleMute,
  onUnmuteAll,
  onSolo,
}: ResultsPageProps) {
  return (
    <>
      <div className="top-bar">
        <span className="top-bar__title">Musicality</span>
        <GenreToggle genre={genre} onGenreChange={onGenreChange} compact />
        <UrlForm
          url={url}
          onUrlChange={onUrlChange}
          onSubmit={onSubmit}
          isLoading={isLoading}
        />
      </div>

      <SongInfo
        title={result.metadata.title}
        tempo={result.tempo}
        genreHint={result.metadata.genre_hint}
      />

      <PlayerControls
        isPlaying={isPlaying}
        currentTime={currentTime}
        duration={duration}
        onToggle={onToggle}
        onSeek={onSeek}
        onSkipForward={onSkipForward}
        onSkipBackward={onSkipBackward}
      />

      <div className="panels">
        <InstrumentGrid
          grid={result.instrument_grid}
          currentBarNum={currentBarNum}
          currentSubdivision={currentSubdivision}
          currentBeatNum={currentBeatNum}
          mutedStems={stemsAvailable ? mutedStems : undefined}
          soloedStem={stemsAvailable ? soloedStem : undefined}
          onToggleMute={stemsAvailable ? onToggleMute : undefined}
          onUnmuteAll={stemsAvailable ? onUnmuteAll : undefined}
          onSolo={stemsAvailable ? onSolo : undefined}
        />
      </div>
    </>
  );
}

import type { GenreOption } from "../types/analysis";
import { GenreToggle } from "../components/GenreToggle";
import { ProcessingStatus } from "../components/ProcessingStatus";
import { UrlForm } from "../components/UrlForm";

interface LandingPageProps {
  url: string;
  onUrlChange: (url: string) => void;
  genre: GenreOption;
  onGenreChange: (genre: GenreOption) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  status: string | null;
  progress: number;
  error: string | null;
}

export function LandingPage({
  url,
  onUrlChange,
  genre,
  onGenreChange,
  onSubmit,
  isLoading,
  status,
  progress,
  error,
}: LandingPageProps) {
  return (
    <div className="landing">
      <h1 className="landing__title">Musicality</h1>
      <p className="landing__subtitle">
        Visualize salsa &amp; bachata music structure
      </p>
      <GenreToggle genre={genre} onGenreChange={onGenreChange} />
      <UrlForm
        url={url}
        onUrlChange={onUrlChange}
        onSubmit={onSubmit}
        isLoading={isLoading}
      />

      {isLoading && status && (
        <ProcessingStatus status={status} progress={progress} />
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

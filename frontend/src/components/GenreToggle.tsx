import type { GenreOption } from "../types/analysis";

interface GenreToggleProps {
  genre: GenreOption;
  onGenreChange: (genre: GenreOption) => void;
  compact?: boolean;
}

export function GenreToggle({ genre, onGenreChange, compact }: GenreToggleProps) {
  return (
    <div className={`genre-toggle ${compact ? "genre-toggle--compact" : ""}`}>
      <button
        className={`genre-toggle__btn ${genre === "bachata" ? "genre-toggle__btn--active" : ""}`}
        onClick={() => onGenreChange("bachata")}
        type="button"
      >
        Bachata
      </button>
      <button
        className={`genre-toggle__btn ${genre === "salsa" ? "genre-toggle__btn--active" : ""}`}
        onClick={() => onGenreChange("salsa")}
        type="button"
      >
        Salsa
      </button>
    </div>
  );
}

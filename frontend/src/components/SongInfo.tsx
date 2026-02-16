interface SongInfoProps {
  title: string;
  tempo: number;
  genreHint: string;
}

export function SongInfo({ title, tempo, genreHint }: SongInfoProps) {
  return (
    <div className="song-info">
      <span className="song-info__title">{title}</span>
      <span className="song-info__meta">
        {Math.round(tempo)} BPM &middot; {genreHint}
      </span>
    </div>
  );
}

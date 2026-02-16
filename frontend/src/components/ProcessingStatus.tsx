const STATUS_LABELS: Record<string, string> = {
  queued: "Queued...",
  downloading: "Downloading audio...",
  detecting_beats: "Detecting beats...",
  separating_stems: "Separating instruments...",
  analyzing_instruments: "Analyzing instruments...",
};

interface ProcessingStatusProps {
  status: string;
  progress: number;
}

export function ProcessingStatus({ status, progress }: ProcessingStatusProps) {
  return (
    <div className="processing-status">
      <div className="processing-status__text">
        {STATUS_LABELS[status] || status}
      </div>
      <div className="processing-status__bar">
        <div
          className="processing-status__fill"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  );
}

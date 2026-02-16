interface UrlFormProps {
  url: string;
  onUrlChange: (url: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
}

export function UrlForm({ url, onUrlChange, onSubmit, isLoading }: UrlFormProps) {
  return (
    <form className="url-form" onSubmit={onSubmit}>
      <input
        className="url-form__input"
        type="text"
        placeholder="Paste a YouTube URL..."
        value={url}
        onChange={(e) => onUrlChange(e.target.value)}
        disabled={isLoading}
      />
      <button
        className="url-form__btn"
        type="submit"
        disabled={isLoading || !url.trim()}
      >
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}

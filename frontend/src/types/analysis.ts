export type GenreHint = "salsa" | "bachata" | "unknown";

export type JobStatus =
  | "queued"
  | "downloading"
  | "detecting_beats"
  | "separating_stems"
  | "analyzing_instruments"
  | "complete"
  | "failed";

export interface Beat {
  time: number;
  beat_num: number;
}

export interface Bar {
  start: number;
  end: number;
  bar_num: number;
}

export interface InstrumentBeat {
  instrument: string;
  beats: boolean[];
  confidence: number;
}

export interface BarInstruments {
  bar_num: number;
  instruments: InstrumentBeat[];
}

export interface InstrumentGrid {
  genre: string;
  instrument_list: string[];
  subdivisions: number;
  bars: BarInstruments[];
}

export interface Metadata {
  title: string;
  duration: number;
  genre_hint: GenreHint;
}

export interface AnalysisResult {
  metadata: Metadata;
  tempo: number;
  beats: Beat[];
  bars: Bar[];
  instrument_grid: InstrumentGrid;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  error: string | null;
  result: AnalysisResult | null;
}

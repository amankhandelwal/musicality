export type GenreHint = "salsa" | "bachata" | "unknown";

export type GenreOption = "salsa" | "bachata";

export interface Beat {
  time: number;
  beat_num: number;
}

export interface Bar {
  start: number;
  end: number;
  bar_num: number;
}

export interface BeatCell {
  active: boolean;
  velocity: number; // 0.0-1.0, normalized onset strength
  pitch: number;    // 0.0-1.0, spectral centroid normalized within freq band
}

export function isBeatCellArray(beats: boolean[] | BeatCell[]): beats is BeatCell[] {
  return beats.length > 0 && typeof beats[0] === "object" && beats[0] !== null && "active" in beats[0];
}

export function normalizeBeatCells(beats: boolean[] | BeatCell[]): BeatCell[] {
  if (isBeatCellArray(beats)) return beats;
  return (beats as boolean[]).map((active) => ({
    active,
    velocity: active ? 0.7 : 0.0,
    pitch: 0.5,
  }));
}

export interface InstrumentBeat {
  instrument: string;
  beats: boolean[] | BeatCell[];
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

// Re-export from split modules for backward compatibility
export type { JobStatus, JobResponse } from "./job";
export type { StemName } from "./audio";

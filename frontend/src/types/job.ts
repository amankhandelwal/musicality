import type { AnalysisResult } from "./analysis";

export type JobStatus =
  | "queued"
  | "downloading"
  | "detecting_beats"
  | "separating_stems"
  | "analyzing_instruments"
  | "complete"
  | "failed";

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  error: string | null;
  result: AnalysisResult | null;
}

import type { GenreOption } from "../types/analysis";
import type { JobResponse } from "../types/job";
import { apiClient } from "./client";

export async function submitAnalysis(
  url: string,
  genre: GenreOption
): Promise<{ job_id: string }> {
  return apiClient.post("/analyze", { url, genre });
}

export async function pollJob(
  jobId: string,
  lastStatus?: string | null,
  lastProgress?: number | null,
  signal?: AbortSignal
): Promise<JobResponse> {
  let path = `/jobs/${jobId}`;
  if (lastStatus !== undefined && lastStatus !== null) {
    const params = new URLSearchParams({
      after_status: lastStatus,
      after_progress: String(lastProgress ?? 0),
    });
    path += `?${params}`;
  }
  return apiClient.get<JobResponse>(path, { signal });
}

import type { StemName } from "../types/audio";
import { apiClient } from "./client";

export function getAudioUrl(jobId: string): string {
  return apiClient.buildUrl(`/audio/${jobId}`);
}

export function getStemUrl(jobId: string, stem: StemName): string {
  return apiClient.buildUrl(`/audio/${jobId}/stems/${stem}`);
}

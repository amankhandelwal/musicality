import { useState, useRef, useCallback } from "react";
import { submitAnalysis, pollJob } from "../api/analysisApi";
import { getAudioUrl } from "../api/audioApi";
import type { AnalysisResult, GenreOption } from "../types/analysis";
import type { JobStatus } from "../types/job";

interface UseAnalysisReturn {
  submit: (url: string, genre: GenreOption) => void;
  status: JobStatus | null;
  progress: number;
  error: string | null;
  result: AnalysisResult | null;
  jobId: string | null;
  audioUrl: string | null;
  isLoading: boolean;
}

export function useAnalysis(): UseAnalysisReturn {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const stopPolling = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  const poll = useCallback(
    (id: string) => {
      const controller = new AbortController();
      abortRef.current = controller;

      (async () => {
        let lastStatus: string | null = null;
        let lastProgress: number | null = null;

        while (!controller.signal.aborted) {
          try {
            const data = await pollJob(id, lastStatus, lastProgress, controller.signal);

            setStatus(data.status);
            setProgress(data.progress);
            lastStatus = data.status;
            lastProgress = data.progress;

            if (data.status === "complete" && data.result) {
              setResult(data.result);
              break;
            } else if (data.status === "failed") {
              setError(data.error || "Analysis failed");
              break;
            }
          } catch (e) {
            if (controller.signal.aborted) return;
            setError(e instanceof Error ? e.message : "Unknown error");
            break;
          }
        }
      })();
    },
    []
  );

  const submit = useCallback(
    async (url: string, genre: GenreOption) => {
      stopPolling();
      setStatus("queued");
      setProgress(0);
      setError(null);
      setResult(null);
      setJobId(null);

      try {
        const data = await submitAnalysis(url, genre);
        setJobId(data.job_id);
        poll(data.job_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        setStatus("failed");
      }
    },
    [poll, stopPolling]
  );

  const audioUrl = jobId ? getAudioUrl(jobId) : null;
  const isLoading =
    status !== null && status !== "complete" && status !== "failed";

  return { submit, status, progress, error, result, jobId, audioUrl, isLoading };
}

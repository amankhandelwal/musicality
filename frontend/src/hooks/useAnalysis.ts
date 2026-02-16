import { useState, useRef, useCallback } from "react";
import type { AnalysisResult, GenreOption, JobResponse, JobStatus } from "../types/analysis";

const API_BASE = "http://localhost:8000";

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
            // Build long-poll URL with last-known state
            let url = `${API_BASE}/jobs/${id}`;
            if (lastStatus !== null) {
              const params = new URLSearchParams({
                after_status: lastStatus,
                after_progress: String(lastProgress ?? 0),
              });
              url += `?${params}`;
            }

            const res = await fetch(url, { signal: controller.signal });
            if (!res.ok) throw new Error("Failed to fetch job status");
            const data: JobResponse = await res.json();

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
        const res = await fetch(`${API_BASE}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, genre }),
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        setJobId(data.job_id);
        poll(data.job_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        setStatus("failed");
      }
    },
    [poll, stopPolling]
  );

  const audioUrl = jobId ? `${API_BASE}/audio/${jobId}` : null;
  const isLoading =
    status !== null && status !== "complete" && status !== "failed";

  return { submit, status, progress, error, result, jobId, audioUrl, isLoading };
}

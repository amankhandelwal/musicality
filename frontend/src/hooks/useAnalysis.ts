import { useState, useRef, useCallback } from "react";
import type { AnalysisResult, JobResponse, JobStatus } from "../types/analysis";

const API_BASE = "http://localhost:8000";

interface UseAnalysisReturn {
  submit: (url: string) => void;
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
  const pollRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const poll = useCallback(
    (id: string) => {
      pollRef.current = window.setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/jobs/${id}`);
          if (!res.ok) throw new Error("Failed to fetch job status");
          const data: JobResponse = await res.json();

          setStatus(data.status);
          setProgress(data.progress);

          if (data.status === "complete" && data.result) {
            setResult(data.result);
            stopPolling();
          } else if (data.status === "failed") {
            setError(data.error || "Analysis failed");
            stopPolling();
          }
        } catch (e) {
          setError(e instanceof Error ? e.message : "Unknown error");
          stopPolling();
        }
      }, 1500);
    },
    [stopPolling]
  );

  const submit = useCallback(
    async (url: string) => {
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
          body: JSON.stringify({ url }),
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

import { useState, useRef, useCallback, useEffect } from "react";
import type { StemName } from "../types/audio";

export type { StemName };
const STEM_NAMES: StemName[] = ["drums", "bass", "vocals", "guitar", "piano", "other"];

export interface StemPlayerReturn {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  isLoading: boolean;
  stemsAvailable: boolean;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (time: number) => void;
  skipForward: () => void;
  skipBackward: () => void;
  load: (baseUrl: string) => void;
  stems: StemName[];
  mutedStems: Set<StemName>;
  toggleMute: (stem: StemName) => void;
  unmuteAll: () => void;
  solo: (stem: StemName | null) => void;
  soloedStem: StemName | null;
}

export function useStemPlayer(): StemPlayerReturn {
  const ctxRef = useRef<AudioContext | null>(null);
  const sourcesRef = useRef<Map<StemName, AudioBufferSourceNode>>(new Map());
  const gainsRef = useRef<Map<StemName, GainNode>>(new Map());
  const buffersRef = useRef<Map<StemName, AudioBuffer>>(new Map());
  const rafRef = useRef<number | null>(null);

  // Fallback HTMLAudioElement for when stems aren't available
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [stemsAvailable, setStemsAvailable] = useState(false);
  const [mutedStems, setMutedStems] = useState<Set<StemName>>(new Set());
  const [soloedStem, setSoloedStem] = useState<StemName | null>(null);

  // Track playback start references for Web Audio scheduling
  const startTimeRef = useRef(0); // AudioContext.currentTime when playback started
  const offsetRef = useRef(0); // offset into the audio buffers

  const stopTick = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const tick = useCallback(() => {
    if (stemsAvailable && ctxRef.current) {
      const elapsed = ctxRef.current.currentTime - startTimeRef.current;
      setCurrentTime(offsetRef.current + elapsed);
    } else if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
    rafRef.current = requestAnimationFrame(tick);
  }, [stemsAvailable]);

  const startTick = useCallback(() => {
    if (rafRef.current === null) {
      rafRef.current = requestAnimationFrame(tick);
    }
  }, [tick]);

  // Stop all Web Audio source nodes
  const stopSources = useCallback(() => {
    sourcesRef.current.forEach((source) => {
      try {
        source.stop();
      } catch {
        // already stopped
      }
    });
    sourcesRef.current.clear();
  }, []);

  // Start all stem sources from a given offset
  const startSources = useCallback((offset: number) => {
    const ctx = ctxRef.current;
    if (!ctx) return;

    stopSources();

    buffersRef.current.forEach((buffer, stem) => {
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      const gain = gainsRef.current.get(stem);
      if (gain) {
        source.connect(gain);
      }
      source.start(0, offset);
      sourcesRef.current.set(stem, source);
    });

    // Handle ended on first source
    const firstSource = sourcesRef.current.values().next().value;
    if (firstSource) {
      firstSource.onended = () => {
        // Only mark as ended if we're near the end of the track
        const ctx = ctxRef.current;
        if (ctx) {
          const elapsed = ctx.currentTime - startTimeRef.current;
          const pos = offsetRef.current + elapsed;
          if (pos >= duration - 0.1) {
            setIsPlaying(false);
            stopTick();
            setCurrentTime(0);
            offsetRef.current = 0;
          }
        }
      };
    }

    startTimeRef.current = ctx.currentTime;
    offsetRef.current = offset;
  }, [stopSources, stopTick, duration]);

  // Apply mute/solo state to gain nodes
  const applyGains = useCallback(
    (muted: Set<StemName>, soloed: StemName | null) => {
      gainsRef.current.forEach((gain, stem) => {
        if (soloed !== null) {
          gain.gain.value = stem === soloed ? 1 : 0;
        } else {
          gain.gain.value = muted.has(stem) ? 0 : 1;
        }
      });
    },
    []
  );

  // Update gains whenever mute/solo state changes
  useEffect(() => {
    if (stemsAvailable) {
      applyGains(mutedStems, soloedStem);
    }
  }, [mutedStems, soloedStem, stemsAvailable, applyGains]);

  const load = useCallback(
    async (baseUrl: string) => {
      stopTick();
      stopSources();
      setIsPlaying(false);
      setCurrentTime(0);
      setDuration(0);
      setIsLoading(true);
      setStemsAvailable(false);
      setMutedStems(new Set());
      setSoloedStem(null);
      offsetRef.current = 0;

      // Clean up old fallback audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      try {
        // Try loading all 6 stems (gracefully handle missing ones)
        const ctx = new AudioContext();
        ctxRef.current = ctx;

        const settled = await Promise.allSettled(
          STEM_NAMES.map(async (stem) => {
            const res = await fetch(`${baseUrl}/stems/${stem}`);
            if (!res.ok) throw new Error(`Failed to fetch ${stem}`);
            const arrayBuf = await res.arrayBuffer();
            const audioBuf = await ctx.decodeAudioData(arrayBuf);
            return [stem, audioBuf] as const;
          })
        );

        const results = settled
          .filter((r): r is PromiseFulfilledResult<readonly [StemName, AudioBuffer]> => r.status === "fulfilled")
          .map((r) => r.value);

        if (results.length === 0) throw new Error("No stems loaded");

        // Create gain nodes
        gainsRef.current.clear();
        buffersRef.current.clear();

        let maxDuration = 0;
        for (const [stem, buffer] of results) {
          buffersRef.current.set(stem, buffer);
          maxDuration = Math.max(maxDuration, buffer.duration);

          const gain = ctx.createGain();
          gain.connect(ctx.destination);
          gainsRef.current.set(stem, gain);
        }

        setDuration(maxDuration);
        setStemsAvailable(true);
        setIsLoading(false);
      } catch {
        // Fallback to mixed audio
        setStemsAvailable(false);

        // Clean up any partial Web Audio state
        if (ctxRef.current) {
          ctxRef.current.close();
          ctxRef.current = null;
        }
        gainsRef.current.clear();
        buffersRef.current.clear();

        const audio = new Audio(baseUrl);
        audio.addEventListener("loadedmetadata", () => {
          setDuration(audio.duration);
        });
        audio.addEventListener("ended", () => {
          setIsPlaying(false);
          stopTick();
        });
        audioRef.current = audio;
        setIsLoading(false);
      }
    },
    [stopTick, stopSources]
  );

  const play = useCallback(() => {
    if (stemsAvailable) {
      const ctx = ctxRef.current;
      if (!ctx) return;
      if (ctx.state === "suspended") {
        ctx.resume();
      }
      startSources(offsetRef.current);
    } else {
      audioRef.current?.play();
    }
    setIsPlaying(true);
    startTick();
  }, [stemsAvailable, startSources, startTick]);

  const pause = useCallback(() => {
    if (stemsAvailable) {
      const ctx = ctxRef.current;
      if (ctx) {
        const elapsed = ctx.currentTime - startTimeRef.current;
        offsetRef.current = offsetRef.current + elapsed;
      }
      stopSources();
    } else {
      audioRef.current?.pause();
    }
    setIsPlaying(false);
    stopTick();
  }, [stemsAvailable, stopSources, stopTick]);

  const toggle = useCallback(() => {
    if (isPlaying) pause();
    else play();
  }, [isPlaying, play, pause]);

  const seek = useCallback(
    (time: number) => {
      const clampedTime = Math.max(0, Math.min(time, duration));
      setCurrentTime(clampedTime);
      offsetRef.current = clampedTime;

      if (stemsAvailable) {
        if (isPlaying) {
          startSources(clampedTime);
        }
      } else if (audioRef.current) {
        audioRef.current.currentTime = clampedTime;
      }
    },
    [stemsAvailable, isPlaying, duration, startSources]
  );

  const skipForward = useCallback(() => {
    const cur = stemsAvailable
      ? offsetRef.current +
        (ctxRef.current
          ? ctxRef.current.currentTime - startTimeRef.current
          : 0)
      : audioRef.current?.currentTime ?? 0;
    seek(cur + 10);
  }, [seek, stemsAvailable]);

  const skipBackward = useCallback(() => {
    const cur = stemsAvailable
      ? offsetRef.current +
        (ctxRef.current
          ? ctxRef.current.currentTime - startTimeRef.current
          : 0)
      : audioRef.current?.currentTime ?? 0;
    seek(cur - 10);
  }, [seek, stemsAvailable]);

  const toggleMute = useCallback((stem: StemName) => {
    setMutedStems((prev) => {
      const next = new Set(prev);
      if (next.has(stem)) next.delete(stem);
      else next.add(stem);
      return next;
    });
  }, []);

  const unmuteAll = useCallback(() => {
    setMutedStems(new Set());
    setSoloedStem(null);
  }, []);

  const solo = useCallback((stem: StemName | null) => {
    setSoloedStem((prev) => (prev === stem ? null : stem));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTick();
      stopSources();
      audioRef.current?.pause();
      if (ctxRef.current) {
        ctxRef.current.close();
      }
    };
  }, [stopTick, stopSources]);

  return {
    isPlaying,
    currentTime,
    duration,
    isLoading,
    stemsAvailable,
    play,
    pause,
    toggle,
    seek,
    skipForward,
    skipBackward,
    load,
    stems: STEM_NAMES,
    mutedStems,
    toggleMute,
    unmuteAll,
    solo,
    soloedStem,
  };
}

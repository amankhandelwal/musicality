import { useState, useRef, useCallback, useEffect } from "react";

interface UseAudioPlayerReturn {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (time: number) => void;
  skipForward: () => void;
  skipBackward: () => void;
  load: (url: string) => void;
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const tick = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const startTick = useCallback(() => {
    if (rafRef.current === null) {
      rafRef.current = requestAnimationFrame(tick);
    }
  }, [tick]);

  const stopTick = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const load = useCallback(
    (url: string) => {
      stopTick();
      if (audioRef.current) {
        audioRef.current.pause();
      }
      const audio = new Audio(url);
      audio.addEventListener("loadedmetadata", () => {
        setDuration(audio.duration);
      });
      audio.addEventListener("ended", () => {
        setIsPlaying(false);
        stopTick();
      });
      audioRef.current = audio;
      setIsPlaying(false);
      setCurrentTime(0);
    },
    [stopTick]
  );

  const play = useCallback(() => {
    audioRef.current?.play();
    setIsPlaying(true);
    startTick();
  }, [startTick]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
    setIsPlaying(false);
    stopTick();
  }, [stopTick]);

  const toggle = useCallback(() => {
    if (isPlaying) pause();
    else play();
  }, [isPlaying, play, pause]);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(time, audioRef.current.duration || 0));
      setCurrentTime(audioRef.current.currentTime);
    }
  }, []);

  const skipForward = useCallback(() => {
    seek((audioRef.current?.currentTime ?? 0) + 10);
  }, [seek]);

  const skipBackward = useCallback(() => {
    seek((audioRef.current?.currentTime ?? 0) - 10);
  }, [seek]);

  useEffect(() => {
    return () => {
      stopTick();
      audioRef.current?.pause();
    };
  }, [stopTick]);

  return {
    isPlaying,
    currentTime,
    duration,
    play,
    pause,
    toggle,
    seek,
    skipForward,
    skipBackward,
    load,
  };
}

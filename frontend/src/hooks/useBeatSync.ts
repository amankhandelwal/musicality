import { useMemo } from "react";
import type { Beat, Bar } from "../types/analysis";

interface BeatSyncState {
  currentBeat: Beat | null;
  currentBeatNum: number;
  currentBarNum: number;
  currentSubdivision: number;
}

export function useBeatSync(
  beats: Beat[],
  bars: Bar[],
  currentTime: number
): BeatSyncState {
  const currentBeatIdx = useMemo(() => {
    return binarySearchFloor(beats, currentTime);
  }, [beats, currentTime]);

  const currentBeat = currentBeatIdx >= 0 ? beats[currentBeatIdx] : null;
  const currentBeatNum = currentBeat ? currentBeat.beat_num : 0;

  // Find current 4/4 bar, then compute 8-count cycle number (pairs of bars)
  const currentBarNum = useMemo(() => {
    const barIdx = binarySearchBarFloor(bars, currentTime);
    if (barIdx < 0) return 0;
    // Pair consecutive bars: bars 0,1 → cycle 0; bars 2,3 → cycle 1; etc.
    return Math.floor(barIdx / 2);
  }, [bars, currentTime]);

  // Compute current subdivision (0-15) within the 8-count cycle
  const currentSubdivision = useMemo(() => {
    if (currentBeatIdx < 0 || beats.length === 0) return 0;

    // The on-beat subdivision is (beatNum - 1) * 2
    const onBeatSubdiv = (currentBeatNum - 1) * 2;
    if (onBeatSubdiv < 0) return 0;

    // Check if we're past the midpoint to the next beat (the "&" position)
    const nextBeatIdx = currentBeatIdx + 1;
    if (nextBeatIdx < beats.length) {
      const midpoint =
        (beats[currentBeatIdx].time + beats[nextBeatIdx].time) / 2;
      if (currentTime >= midpoint) {
        return Math.min(onBeatSubdiv + 1, 15);
      }
    }

    return Math.min(onBeatSubdiv, 15);
  }, [beats, currentBeatIdx, currentBeatNum, currentTime]);

  return {
    currentBeat,
    currentBeatNum,
    currentBarNum,
    currentSubdivision,
  };
}

function binarySearchFloor(beats: Beat[], time: number): number {
  let lo = 0;
  let hi = beats.length - 1;
  let result = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >>> 1;
    if (beats[mid].time <= time) {
      result = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return result;
}

function binarySearchBarFloor(bars: Bar[], time: number): number {
  let lo = 0;
  let hi = bars.length - 1;
  let result = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >>> 1;
    if (bars[mid].start <= time) {
      result = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return result;
}

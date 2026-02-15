import { useMemo, useState, useEffect, useCallback } from "react";
import type { InstrumentGrid as InstrumentGridType } from "../types/analysis";
import "./InstrumentGrid.css";

interface InstrumentGridProps {
  grid: InstrumentGridType;
  currentBarNum: number;
  currentSubdivision: number;
  currentBeatNum: number;
}

const DISPLAY_NAMES: Record<string, string> = {
  guira: "Guira",
  bongo: "Bongo",
  bass_guitar: "Bass",
  lead_guitar: "Lead Gtr",
  rhythm_guitar: "Rhy Gtr",
  voice: "Voice",
  conga: "Conga",
  timbales: "Timbales",
  cowbell: "Cowbell",
  claves: "Claves",
  maracas_guiro: "Maracas",
  piano: "Piano",
  trumpet: "Trumpet",
  trombone: "Trombone",
};

const INSTRUMENT_ORDER = [
  "guira", "bongo", "conga", "timbales", "cowbell", "claves", "maracas_guiro",
  "bass_guitar", "rhythm_guitar", "lead_guitar", "piano",
  "voice", "trumpet", "trombone",
];

// Instrument group colors
const PERCUSSION = new Set(["guira", "bongo", "conga", "timbales", "cowbell", "claves", "maracas_guiro"]);

const PINNED_KEY = "musicality_pinned_instruments";

function loadPinned(): Set<string> {
  try {
    const raw = localStorage.getItem(PINNED_KEY);
    if (raw) return new Set(JSON.parse(raw));
  } catch { /* ignore */ }
  return new Set();
}

function savePinned(pinned: Set<string>) {
  localStorage.setItem(PINNED_KEY, JSON.stringify([...pinned]));
}

export function InstrumentGrid({
  grid,
  currentBarNum,
  currentSubdivision,
  currentBeatNum,
}: InstrumentGridProps) {
  const subdivisions = grid.subdivisions ?? 16;
  const [pinned, setPinned] = useState<Set<string>>(loadPinned);

  useEffect(() => {
    savePinned(pinned);
  }, [pinned]);

  const togglePin = useCallback((instrument: string) => {
    setPinned((prev) => {
      const next = new Set(prev);
      if (next.has(instrument)) next.delete(instrument);
      else next.add(instrument);
      return next;
    });
  }, []);

  const currentBar = useMemo(() => {
    return grid.bars.find((b) => b.bar_num === currentBarNum) ?? null;
  }, [grid.bars, currentBarNum]);

  const rawInstruments = currentBar?.instruments ?? [];

  // Sort instruments by canonical order, with pinned on top
  const sortedInstruments = useMemo(() => {
    const sorted = [...rawInstruments].sort((a, b) => {
      const ai = INSTRUMENT_ORDER.indexOf(a.instrument);
      const bi = INSTRUMENT_ORDER.indexOf(b.instrument);
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    });
    const pinnedList = sorted.filter((i) => pinned.has(i.instrument));
    const unpinnedList = sorted.filter((i) => !pinned.has(i.instrument));
    return { pinnedList, unpinnedList };
  }, [rawInstruments, pinned]);

  if (rawInstruments.length === 0) {
    return (
      <div className="instrument-grid">
        <span className="instrument-grid__empty">Waiting for data...</span>
      </div>
    );
  }

  const colTemplate = `72px repeat(${subdivisions}, 1fr)`;

  const renderBeatHeader = () => (
    <div
      className="instrument-grid__row instrument-grid__header"
      style={{ gridTemplateColumns: colTemplate }}
    >
      <div className="instrument-grid__label" />
      {Array.from({ length: subdivisions }, (_, i) => {
        const isOnBeat = i % 2 === 0;
        const beatNum = Math.floor(i / 2) + 1;
        const isCurrent = currentSubdivision === i;
        return (
          <div
            key={i}
            className={`instrument-grid__beat-header${
              !isOnBeat ? " instrument-grid__beat-header--and" : ""
            }${isCurrent ? " instrument-grid__beat-header--active" : ""}`}
          >
            {isOnBeat ? beatNum : "&"}
          </div>
        );
      })}
    </div>
  );

  const renderRow = (inst: { instrument: string; beats: boolean[]; confidence: number }) => (
    <div
      key={inst.instrument}
      className="instrument-grid__row"
      style={{ gridTemplateColumns: colTemplate }}
    >
      <div className="instrument-grid__label">
        <button
          className={`instrument-grid__pin ${pinned.has(inst.instrument) ? "instrument-grid__pin--active" : ""}`}
          onClick={() => togglePin(inst.instrument)}
          title={pinned.has(inst.instrument) ? "Unpin" : "Pin to top"}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill={pinned.has(inst.instrument) ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
            <path d="M12 2L12 12M12 12L8 8M12 12L16 8M5 21L12 14L19 21" />
          </svg>
        </button>
        <span className="instrument-grid__instrument-name">
          {DISPLAY_NAMES[inst.instrument] || inst.instrument}
        </span>
      </div>
      {inst.beats.slice(0, subdivisions).map((active, i) => {
        const isCurrent = currentSubdivision === i;
        const isPast = i < currentSubdivision;
        const isPerc = PERCUSSION.has(inst.instrument);
        let cellClass = "instrument-grid__cell";
        if (active) cellClass += " instrument-grid__cell--active";
        if (isCurrent) cellClass += " instrument-grid__cell--current";
        if (isPast && active) cellClass += " instrument-grid__cell--past";
        if (active && isPerc) cellClass += " instrument-grid__cell--perc";
        if (active && !isPerc) cellClass += " instrument-grid__cell--melodic";
        return (
          <div
            key={i}
            className={cellClass}
            style={active ? { opacity: Math.max(0.5, inst.confidence) } : undefined}
          />
        );
      })}
    </div>
  );

  return (
    <div className="instrument-grid">
      <div className="instrument-grid__table">
        {renderBeatHeader()}
        {sortedInstruments.pinnedList.length > 0 && (
          <>
            {sortedInstruments.pinnedList.map(renderRow)}
            <div className="instrument-grid__divider" />
          </>
        )}
        {sortedInstruments.unpinnedList.map(renderRow)}
      </div>
    </div>
  );
}

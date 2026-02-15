import { useMemo, useState, useEffect, useCallback } from "react";
import type { InstrumentGrid as InstrumentGridType } from "../types/analysis";
import type { StemName } from "../hooks/useStemPlayer";
import "./InstrumentGrid.css";

interface InstrumentGridProps {
  grid: InstrumentGridType;
  currentBarNum: number;
  currentSubdivision: number;
  currentBeatNum: number;
  mutedStems?: Set<StemName>;
  soloedStem?: StemName | null;
  onToggleMute?: (stem: StemName) => void;
  onUnmuteAll?: () => void;
  onSolo?: (stem: StemName | null) => void;
}

const DISPLAY_NAMES: Record<string, string> = {
  guira: "Guira",
  bongo: "Bongo",
  bass_guitar: "Bass Guitar",
  lead_guitar: "Lead Guitar",
  rhythm_guitar: "Rhythm Guitar",
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

const PERCUSSION = new Set(["guira", "bongo", "conga", "timbales", "cowbell", "claves", "maracas_guiro"]);

const INSTRUMENT_STEM: Record<string, StemName> = {
  guira: "drums",
  bongo: "drums",
  conga: "drums",
  timbales: "drums",
  cowbell: "drums",
  claves: "drums",
  maracas_guiro: "drums",
  bass_guitar: "bass",
  voice: "vocals",
  rhythm_guitar: "other",
  lead_guitar: "other",
  piano: "other",
  trumpet: "other",
  trombone: "other",
};

const STEM_ORDER: StemName[] = ["drums", "bass", "vocals", "other"];

const STEM_CONFIG: Record<StemName, { label: string; color: string }> = {
  drums: { label: "Drums", color: "#f59e0b" },
  bass: { label: "Bass", color: "#3b82f6" },
  vocals: { label: "Vocals", color: "#ec4899" },
  other: { label: "Other", color: "#a855f7" },
};

type InstrumentBeat = { instrument: string; beats: boolean[]; confidence: number };

type StemGroup = {
  stem: StemName;
  label: string;
  color: string;
  instruments: InstrumentBeat[];
};

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

function buildStemGroups(instruments: InstrumentBeat[]): StemGroup[] {
  const byStem = new Map<StemName, InstrumentBeat[]>();
  for (const inst of instruments) {
    const stem = INSTRUMENT_STEM[inst.instrument];
    if (!stem) continue;
    if (!byStem.has(stem)) byStem.set(stem, []);
    byStem.get(stem)!.push(inst);
  }

  const groups: StemGroup[] = [];
  for (const stem of STEM_ORDER) {
    const insts = byStem.get(stem);
    if (!insts || insts.length === 0) continue;
    const config = STEM_CONFIG[stem];
    insts.sort((a, b) => {
      const ai = INSTRUMENT_ORDER.indexOf(a.instrument);
      const bi = INSTRUMENT_ORDER.indexOf(b.instrument);
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    });
    groups.push({
      stem,
      label: config.label,
      color: config.color,
      instruments: insts,
    });
  }
  return groups;
}

export function InstrumentGrid({
  grid,
  currentBarNum,
  currentSubdivision,
  currentBeatNum,
  mutedStems,
  soloedStem,
  onToggleMute,
  onUnmuteAll,
  onSolo,
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

  const { pinnedGroups, unpinnedGroups } = useMemo(() => {
    const pinnedList = rawInstruments.filter((i) => pinned.has(i.instrument));
    const unpinnedList = rawInstruments.filter((i) => !pinned.has(i.instrument));
    return {
      pinnedGroups: buildStemGroups(pinnedList),
      unpinnedGroups: buildStemGroups(unpinnedList),
    };
  }, [rawInstruments, pinned]);

  if (rawInstruments.length === 0) {
    return (
      <div className="instrument-grid">
        <span className="instrument-grid__empty">Waiting for data...</span>
      </div>
    );
  }

  const colTemplate = `145px repeat(${subdivisions}, 1fr)`;

  const hasStemControls = !!onToggleMute;

  const hasAnyMuteOrSolo =
    (mutedStems && mutedStems.size > 0) || (soloedStem !== undefined && soloedStem !== null);

  const isInstrumentMuted = (instrument: string): boolean => {
    const stem = INSTRUMENT_STEM[instrument];
    if (!stem) return false;
    if (soloedStem !== undefined && soloedStem !== null) return stem !== soloedStem;
    if (mutedStems) return mutedStems.has(stem);
    return false;
  };

  const isStemMuted = (stem: StemName): boolean => {
    if (soloedStem !== undefined && soloedStem !== null) return stem !== soloedStem;
    if (mutedStems) return mutedStems.has(stem);
    return false;
  };

  const renderRow = (inst: InstrumentBeat) => {
    const muted = isInstrumentMuted(inst.instrument);
    const isPinned = pinned.has(inst.instrument);
    return (
      <div
        key={inst.instrument}
        className={`instrument-grid__row${muted ? " instrument-grid__row--muted" : ""}`}
        style={{ gridTemplateColumns: colTemplate }}
      >
        <div className="instrument-grid__label">
          <button
            className={`instrument-grid__pin ${isPinned ? "instrument-grid__pin--active" : ""}`}
            onClick={() => togglePin(inst.instrument)}
            title={isPinned ? "Unpin" : "Pin to top"}
          >
            {isPinned ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="0.5">
                <path d="M17.1 2.6a1 1 0 0 1 1.4 0l2.9 2.9a1 1 0 0 1 0 1.4l-3.5 3.5.7 3.8a1 1 0 0 1-.3.9l-2.1 2.1a1 1 0 0 1-1.4 0L11 13.4l-4.3 4.3a1 1 0 0 1-1.4-1.4l4.3-4.3-3.8-3.8a1 1 0 0 1 0-1.4l2.1-2.1a1 1 0 0 1 .9-.3l3.8.7 3.5-3.5z" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.1 2.6a1 1 0 0 1 1.4 0l2.9 2.9a1 1 0 0 1 0 1.4l-3.5 3.5.7 3.8a1 1 0 0 1-.3.9l-2.1 2.1a1 1 0 0 1-1.4 0L11 13.4l-4.3 4.3a1 1 0 0 1-1.4-1.4l4.3-4.3-3.8-3.8a1 1 0 0 1 0-1.4l2.1-2.1a1 1 0 0 1 .9-.3l3.8.7 3.5-3.5z" />
              </svg>
            )}
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
  };

  const renderStemGroup = (group: StemGroup) => {
    const muted = isStemMuted(group.stem);
    const isMutedDirectly = mutedStems?.has(group.stem) ?? false;
    const isSoloed = soloedStem === group.stem;
    return (
      <div key={group.stem} className="instrument-grid__stem-group">
        {hasStemControls && (
          <div className={`instrument-grid__stem-controls${muted ? " instrument-grid__stem-controls--muted" : ""}`}>
            <div
              className="instrument-grid__stem-bar"
              style={{ background: group.color }}
            />
            <div className="instrument-grid__stem-btns">
              <button
                className={`instrument-grid__stem-btn${isMutedDirectly ? " instrument-grid__stem-btn--mute-active" : ""}`}
                onClick={() => onToggleMute!(group.stem)}
                title={isMutedDirectly ? "Unmute" : "Mute"}
              >
                {isMutedDirectly ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 5L6 9H2v6h4l5 4V5z" />
                    <line x1="23" y1="9" x2="17" y2="15" />
                    <line x1="17" y1="9" x2="23" y2="15" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 5L6 9H2v6h4l5 4V5z" />
                    <path d="M15.54 8.46a5 5 0 010 7.07" />
                  </svg>
                )}
                <span className="instrument-grid__stem-btn-label">
                  {isMutedDirectly ? "Off" : "On"}
                </span>
              </button>
              <button
                className={`instrument-grid__stem-btn${isSoloed ? " instrument-grid__stem-btn--solo-active" : ""}`}
                onClick={() => onSolo!(group.stem)}
                title={isSoloed ? "Unsolo" : "Solo"}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
                </svg>
                <span className="instrument-grid__stem-btn-label">Solo</span>
              </button>
            </div>
          </div>
        )}
        <div className="instrument-grid__stem-rows">
          {group.instruments.map(renderRow)}
        </div>
      </div>
    );
  };

  const stemControlsWidth = hasStemControls ? 87 : 0; // bar(3) + gap(6) + btns(72) + gap(6)

  const renderBeatHeader = () => (
    <div
      className="instrument-grid__row instrument-grid__header"
      style={{
        gridTemplateColumns: colTemplate,
        marginLeft: hasStemControls ? stemControlsWidth : undefined,
      }}
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

  return (
    <div className="instrument-grid">
      {hasStemControls && hasAnyMuteOrSolo && (
        <div className="instrument-grid__toolbar">
          <button
            className="instrument-grid__unmute-all-btn"
            onClick={onUnmuteAll}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 5L6 9H2v6h4l5 4V5z" />
              <path d="M19.07 4.93a10 10 0 010 14.14" />
              <path d="M15.54 8.46a5 5 0 010 7.07" />
            </svg>
            Unmute All
          </button>
        </div>
      )}
      <div className="instrument-grid__table">
        {renderBeatHeader()}
        {pinnedGroups.length > 0 && (
          <>
            {pinnedGroups.map(renderStemGroup)}
            <div className="instrument-grid__divider" />
          </>
        )}
        {unpinnedGroups.map(renderStemGroup)}
      </div>
    </div>
  );
}

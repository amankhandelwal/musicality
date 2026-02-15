import { useMemo } from "react";
import type { InstrumentGrid as InstrumentGridType } from "../types/analysis";
import "./InstrumentGrid.css";

interface InstrumentGridProps {
  grid: InstrumentGridType;
  currentBarNum: number;
  currentSubdivision: number;
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

const SUBDIV_HEADERS = [
  "1", "&", "2", "&", "3", "&", "4", "&",
  "5", "&", "6", "&", "7", "&", "8", "&",
];

export function InstrumentGrid({
  grid,
  currentBarNum,
  currentSubdivision,
}: InstrumentGridProps) {
  const subdivisions = grid.subdivisions ?? 16;

  const currentBar = useMemo(() => {
    return grid.bars.find((b) => b.bar_num === currentBarNum) ?? null;
  }, [grid.bars, currentBarNum]);

  const instruments = currentBar?.instruments ?? [];

  if (instruments.length === 0) {
    return (
      <div className="instrument-grid">
        <h3 className="instrument-grid__title">Instruments</h3>
        <span className="instrument-grid__empty">--</span>
      </div>
    );
  }

  return (
    <div className="instrument-grid">
      <h3 className="instrument-grid__title">Instruments</h3>
      <div className="instrument-grid__table">
        {/* Header row */}
        <div
          className="instrument-grid__row instrument-grid__header"
          style={{
            gridTemplateColumns: `80px repeat(${subdivisions}, 1fr)`,
          }}
        >
          <div className="instrument-grid__label" />
          {SUBDIV_HEADERS.slice(0, subdivisions).map((label, i) => (
            <div
              key={i}
              className={`instrument-grid__beat-header ${
                i % 2 === 1 ? "instrument-grid__beat-header--and" : ""
              } ${
                currentSubdivision === i
                  ? "instrument-grid__beat-header--active"
                  : ""
              }`}
            >
              {label}
            </div>
          ))}
        </div>

        {/* Instrument rows */}
        {instruments.map((inst) => (
          <div
            key={inst.instrument}
            className="instrument-grid__row"
            style={{
              gridTemplateColumns: `80px repeat(${subdivisions}, 1fr)`,
            }}
          >
            <div className="instrument-grid__label">
              {DISPLAY_NAMES[inst.instrument] || inst.instrument}
            </div>
            {inst.beats.slice(0, subdivisions).map((active, i) => (
              <div
                key={i}
                className={`instrument-grid__cell ${
                  active ? "instrument-grid__cell--active" : ""
                } ${
                  currentSubdivision === i
                    ? "instrument-grid__cell--current"
                    : ""
                }`}
                style={{
                  opacity: active ? Math.max(0.4, inst.confidence) : undefined,
                }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

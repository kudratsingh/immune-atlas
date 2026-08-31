"use client";

import { AxisLeft } from "@visx/axis";
import { scaleLinear } from "@visx/scale";
import { Line } from "@visx/shape";
import { useMemo, useState } from "react";

import { PALETTE, responseColour, type ResponseGroup } from "@/lib/palette";
import { formatPercentage } from "@/lib/stats-format";

import { DataTable, type DataColumn } from "../tables/DataTable";
import { useReducedMotion } from "./useReducedMotion";

export interface BoxPlotPoint {
  sample: string;
  subject: string;
  time: number;
  percentage: number;
  response: ResponseGroup;
}

interface BoxSummary {
  q1: number;
  median: number;
  q3: number;
  low: number;
  high: number;
}

export function quantile(sorted: number[], probability: number): number {
  if (sorted.length === 0) return 0;
  const index = (sorted.length - 1) * probability;
  const lower = Math.floor(index);
  const upper = sorted[lower + 1];
  if (upper === undefined) return sorted[lower];
  return sorted[lower] + (upper - sorted[lower]) * (index - lower);
}

export function summarise(values: number[]): BoxSummary {
  const sorted = [...values].sort((left, right) => left - right);
  const q1 = quantile(sorted, 0.25);
  const median = quantile(sorted, 0.5);
  const q3 = quantile(sorted, 0.75);
  const iqr = q3 - q1;
  const lowBound = q1 - 1.5 * iqr;
  const highBound = q3 + 1.5 * iqr;
  return {
    q1,
    median,
    q3,
    low: sorted.find((value) => value >= lowBound) ?? sorted[0] ?? 0,
    high: [...sorted].reverse().find((value) => value <= highBound) ?? sorted.at(-1) ?? 0,
  };
}

function hashJitter(value: string): number {
  let hash = 0;
  for (const character of value) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  return (hash % 1000) / 1000 - 0.5;
}

const groupLabel: Record<ResponseGroup, string> = { yes: "Responders", no: "Non-responders" };

export function BoxPlot({
  title,
  points,
  width = 360,
  height = 300,
}: {
  title: string;
  points: BoxPlotPoint[];
  width?: number;
  height?: number;
}) {
  const [showTable, setShowTable] = useState(false);
  const [activePoint, setActivePoint] = useState<BoxPlotPoint | null>(null);
  const reducedMotion = useReducedMotion();
  const groups = useMemo(
    () => ({
      yes: points.filter((point) => point.response === "yes"),
      no: points.filter((point) => point.response === "no"),
    }),
    [points],
  );
  const margin = { top: 16, right: 16, bottom: 44, left: 48 };
  const maxValue = Math.max(...points.map((point) => point.percentage), 1);
  const y = scaleLinear({
    domain: [0, Math.ceil(maxValue / 5) * 5],
    range: [height - margin.bottom, margin.top],
    nice: true,
  });
  const positions: Record<ResponseGroup, number> = { yes: width * 0.34, no: width * 0.74 };
  const columns: DataColumn<BoxPlotPoint>[] = [
    { id: "sample", header: "Sample", render: (point) => <code>{point.sample}</code> },
    { id: "subject", header: "Subject", render: (point) => <code>{point.subject}</code> },
    { id: "response", header: "Group", render: (point) => groupLabel[point.response] },
    { id: "time", header: "Day", numeric: true, render: (point) => point.time },
    {
      id: "percentage",
      header: "Frequency",
      numeric: true,
      render: (point) => formatPercentage(point.percentage),
    },
  ];

  return (
    <section className="chart-panel" aria-labelledby={`chart-${title.replaceAll(" ", "-")}`}>
      <div className="chart-heading">
        <h3 id={`chart-${title.replaceAll(" ", "-")}`}>{title}</h3>
        <button
          type="button"
          aria-pressed={showTable}
          onClick={() => setShowTable((value) => !value)}
        >
          {showTable ? "Show chart" : "Show as table"}
        </button>
      </div>
      {showTable ? (
        <DataTable
          caption={`${title} values by response group`}
          columns={columns}
          rows={points}
          getRowKey={(point) => `${point.sample}-${point.response}`}
        />
      ) : (
        <div className="chart-surface" data-reduced-motion={reducedMotion}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            role="img"
            aria-label={`${title} distribution by response group`}
          >
            {y.ticks(5).map((tick) => (
              <Line
                from={{ x: margin.left, y: y(tick) }}
                key={tick}
                stroke={PALETTE.rule}
                strokeWidth={1}
                to={{ x: width - margin.right, y: y(tick) }}
              />
            ))}
            <AxisLeft
              left={margin.left}
              scale={y}
              numTicks={5}
              stroke={PALETTE.inkMuted}
              tickStroke={PALETTE.inkMuted}
              tickFormat={(value) => `${value}%`}
              tickLabelProps={() => ({
                fill: PALETTE.inkMuted,
                fontSize: 11,
                textAnchor: "end",
                dy: "0.33em",
              })}
            />
            {(["yes", "no"] as const).map((group) => {
              const groupPoints = groups[group];
              if (groupPoints.length === 0) return null;
              const summary = summarise(groupPoints.map((point) => point.percentage));
              const x = positions[group];
              const colour = responseColour(group);
              return (
                <g key={group}>
                  {groupPoints.map((point) => (
                    <circle
                      key={`${point.sample}-${point.time}`}
                      cx={x + hashJitter(`${point.sample}-${point.time}`) * 40}
                      cy={y(point.percentage)}
                      r={activePoint === point ? 5 : 3}
                      fill={colour}
                      fillOpacity={activePoint === point ? 1 : 0.38}
                      stroke={activePoint === point ? PALETTE.panel : "none"}
                      strokeWidth={activePoint === point ? 2 : 0}
                      tabIndex={0}
                      aria-label={`${point.sample}, ${groupLabel[group]}, day ${point.time}, ${formatPercentage(point.percentage)}`}
                      onMouseEnter={() => setActivePoint(point)}
                      onMouseLeave={() => setActivePoint(null)}
                      onFocus={() => setActivePoint(point)}
                      onBlur={() => setActivePoint(null)}
                    />
                  ))}
                  <Line
                    from={{ x, y: y(summary.low) }}
                    to={{ x, y: y(summary.high) }}
                    stroke={colour}
                  />
                  <Line
                    from={{ x: x - 12, y: y(summary.low) }}
                    to={{ x: x + 12, y: y(summary.low) }}
                    stroke={colour}
                  />
                  <Line
                    from={{ x: x - 12, y: y(summary.high) }}
                    to={{ x: x + 12, y: y(summary.high) }}
                    stroke={colour}
                  />
                  <rect
                    x={x - 26}
                    y={y(summary.q3)}
                    width={52}
                    height={Math.max(1, y(summary.q1) - y(summary.q3))}
                    fill={colour}
                    fillOpacity={0.1}
                    rx={3}
                    stroke={colour}
                    strokeWidth={1.25}
                  />
                  <Line
                    from={{ x: x - 26, y: y(summary.median) }}
                    to={{ x: x + 26, y: y(summary.median) }}
                    stroke={colour}
                    strokeWidth={2.5}
                  />
                  <text
                    x={x}
                    y={height - 22}
                    textAnchor="middle"
                    fill={PALETTE.inkMuted}
                    fontSize={11}
                  >
                    {groupLabel[group]} n={groupPoints.length}
                  </text>
                </g>
              );
            })}
          </svg>
          {activePoint ? (
            <div className="chart-tooltip" role="status">
              <strong>{formatPercentage(activePoint.percentage)}</strong> —{" "}
              <code>{activePoint.sample}</code>, {activePoint.subject}, day {activePoint.time}
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}

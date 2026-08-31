"use client";

import { scaleLinear } from "@visx/scale";
import { Bar } from "@visx/shape";
import { useState } from "react";

import { PALETTE } from "@/lib/palette";
import { formatCount } from "@/lib/stats-format";

import { DataTable, type DataColumn } from "../tables/DataTable";
import { useReducedMotion } from "./useReducedMotion";

export interface DistributionBarDatum {
  label: string;
  value: number;
}

export function DistributionBars({
  title,
  unit,
  data,
}: {
  title: string;
  unit: string;
  data: DistributionBarDatum[];
}) {
  const [showTable, setShowTable] = useState(false);
  const reducedMotion = useReducedMotion();
  const width = 520;
  const rowHeight = 42;
  const left = 110;
  const max = Math.max(...data.map((datum) => datum.value), 1);
  const x = scaleLinear({ domain: [0, max], range: [0, width - left - 64] });
  const columns: DataColumn<DistributionBarDatum>[] = [
    { id: "label", header: "Group", render: (datum) => datum.label },
    { id: "value", header: unit, numeric: true, render: (datum) => formatCount(datum.value) },
  ];
  return (
    <section className="chart-panel" aria-labelledby={`bars-${title.replaceAll(" ", "-")}`}>
      <div className="chart-heading">
        <div>
          <h3 id={`bars-${title.replaceAll(" ", "-")}`}>{title}</h3>
          <p>{unit}</p>
        </div>
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
          caption={`${title}, ${unit}`}
          columns={columns}
          rows={data}
          getRowKey={(datum) => datum.label}
        />
      ) : (
        <div className="chart-surface" data-reduced-motion={reducedMotion}>
          <svg
            viewBox={`0 0 ${width} ${Math.max(1, data.length) * rowHeight + 8}`}
            role="img"
            aria-label={`${title}, ${unit}`}
          >
            {data.map((datum, index) => {
              const y = index * rowHeight + 8;
              return (
                <g key={datum.label}>
                  <text x={0} y={y + 20} fill={PALETTE.ink} fontSize={13}>
                    {datum.label}
                  </text>
                  <Bar
                    x={left}
                    y={y}
                    width={x(datum.value)}
                    height={26}
                    fill={PALETTE.populations[1]}
                  />
                  <text
                    x={left + x(datum.value) + 8}
                    y={y + 19}
                    fill={PALETTE.ink}
                    fontSize={13}
                    fontWeight={600}
                  >
                    {formatCount(datum.value)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      )}
    </section>
  );
}

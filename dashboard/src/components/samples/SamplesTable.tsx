"use client";

import { Fragment, useState } from "react";

import type { BundleSample } from "@/lib/filters";
import {
  compositionFor,
  percentageSum,
  sumsToOneHundred,
  type PopulationInfo,
  type SortDirection,
  type SortKey,
} from "@/lib/samples-view";
import { formatCount, formatPercentage } from "@/lib/stats-format";

const SORTABLE_COLUMNS: { key: SortKey; header: string; numeric?: boolean }[] = [
  { key: "sample", header: "Sample" },
  { key: "subject", header: "Subject" },
  { key: "condition", header: "Condition" },
  { key: "treatment", header: "Treatment" },
  { key: "time", header: "Day", numeric: true },
  { key: "response", header: "Response" },
  { key: "total_count", header: "Total count", numeric: true },
];

function CompositionBar({
  sample,
  populations,
}: {
  sample: BundleSample;
  populations: PopulationInfo[];
}) {
  const segments = compositionFor(sample, populations);
  const description = segments
    .map((segment) => `${segment.displayName} ${formatPercentage(segment.percentage)}`)
    .join(", ");
  return (
    <div aria-label={`Composition: ${description}`} className="composition-bar" role="img">
      {segments.map((segment) => (
        <span
          className={`composition-segment population-${segment.colourIndex + 1}`}
          key={segment.name}
          style={{ width: `${segment.percentage}%` }}
          title={`${segment.displayName}: ${formatPercentage(segment.percentage)}`}
        />
      ))}
    </div>
  );
}

export function SamplesTable({
  samples,
  populations,
  sortKey,
  sortDirection,
  onSort,
}: {
  samples: BundleSample[];
  populations: PopulationInfo[];
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
}) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="table-scroll" role="region" aria-label="Samples, scrollable" tabIndex={0}>
      <table className="data-table samples-table">
        <caption className="visually-hidden">Samples with per-population composition</caption>
        <thead>
          <tr>
            {SORTABLE_COLUMNS.map((column) => (
              <th
                aria-sort={
                  sortKey === column.key
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : undefined
                }
                className={column.numeric ? "numeric" : undefined}
                key={column.key}
                scope="col"
              >
                <button className="sort-button" onClick={() => onSort(column.key)} type="button">
                  {column.header}
                  {sortKey === column.key ? (
                    <svg
                      aria-hidden="true"
                      className="sort-caret"
                      fill="none"
                      height="12"
                      viewBox="0 0 12 12"
                      width="12"
                    >
                      <path
                        d={
                          sortDirection === "asc"
                            ? "M6 2.5v7M3 5l3-2.5L9 5"
                            : "M6 9.5v-7M3 7l3 2.5L9 7"
                        }
                        stroke="currentColor"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="1.6"
                      />
                    </svg>
                  ) : null}
                </button>
              </th>
            ))}
            <th scope="col">Composition</th>
            <th className="numeric" scope="col">
              Sum
            </th>
            <th scope="col">
              <span className="visually-hidden">Details</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {samples.map((sample) => (
            <Fragment key={sample.sample}>
              <tr>
                <td className="pinned">
                  <code>{sample.sample}</code>
                </td>
                <td>
                  <code>{sample.subject}</code>
                </td>
                <td>{sample.condition}</td>
                <td>{sample.treatment}</td>
                <td className="numeric">{sample.time}</td>
                <td>{sample.response ?? "not applicable"}</td>
                <td className="numeric">{formatCount(sample.total_count)}</td>
                <td className="composition-cell">
                  <CompositionBar populations={populations} sample={sample} />
                </td>
                <td className="numeric">
                  {sumsToOneHundred(sample) ? "100%" : formatPercentage(percentageSum(sample), 4)}
                </td>
                <td>
                  <button
                    aria-expanded={expanded === sample.sample}
                    className="row-toggle"
                    onClick={() => setExpanded(expanded === sample.sample ? null : sample.sample)}
                    type="button"
                  >
                    {expanded === sample.sample ? "Hide" : "Show"} percentages
                  </button>
                </td>
              </tr>
              {expanded === sample.sample ? (
                <tr className="expanded-row">
                  <td colSpan={SORTABLE_COLUMNS.length + 3}>
                    <dl className="composition-detail">
                      {compositionFor(sample, populations).map((segment) => (
                        <div key={segment.name}>
                          <dt>{segment.displayName}</dt>
                          <dd>
                            {formatCount(sample.counts[segment.name as keyof typeof sample.counts])}{" "}
                            cells, {formatPercentage(segment.percentage)}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </td>
                </tr>
              ) : null}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

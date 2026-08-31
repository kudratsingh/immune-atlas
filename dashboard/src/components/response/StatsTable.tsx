"use client";

import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import type { Comparison, ComparisonRow } from "@/lib/response-view";
import { formatCount, formatEffectSize, formatPValue } from "@/lib/stats-format";

function median(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "n/a";
  return value.toFixed(2);
}

function interval(value: number[] | null): string {
  if (!value || value.length < 2) return "n/a";
  return `${value[0].toFixed(2)}–${value[1].toFixed(2)}`;
}

function statistic(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "n/a";
  return formatCount(value);
}

export function StatsTable({
  comparison,
  names,
}: {
  comparison: Comparison;
  names: ReadonlyMap<string, string>;
}) {
  const unitLabel = comparison.unit === "subject" ? "subjects" : "samples";
  const columns: DataColumn<ComparisonRow>[] = [
    {
      id: "population",
      header: "Population",
      render: (row) => names.get(row.population) ?? row.population,
    },
    { id: "n_yes", header: `Responder ${unitLabel}`, numeric: true, render: (row) => row.n_yes },
    {
      id: "n_no",
      header: `Non-responder ${unitLabel}`,
      numeric: true,
      render: (row) => row.n_no,
    },
    {
      id: "median_yes",
      header: "Median % (R)",
      numeric: true,
      render: (row) => median(row.median_yes),
    },
    {
      id: "median_no",
      header: "Median % (NR)",
      numeric: true,
      render: (row) => median(row.median_no),
    },
    { id: "iqr_yes", header: "IQR (R)", numeric: true, render: (row) => interval(row.iqr_yes) },
    { id: "iqr_no", header: "IQR (NR)", numeric: true, render: (row) => interval(row.iqr_no) },
    { id: "u", header: "U", numeric: true, render: (row) => statistic(row.u_statistic) },
    { id: "p", header: "p", numeric: true, render: (row) => formatPValue(row.p_value) },
    { id: "q", header: "q", numeric: true, render: (row) => formatPValue(row.q_value) },
    {
      id: "effect",
      header: "Effect size r",
      numeric: true,
      render: (row) => formatEffectSize(row.effect_size),
    },
    {
      id: "welch",
      header: "Welch p",
      numeric: true,
      render: (row) => formatPValue(row.welch_p),
    },
    {
      id: "significant",
      header: "q < 0.05",
      render: (row) => (row.significant_adjusted ? "yes" : "no"),
    },
  ];
  return (
    <DataTable
      caption={`Response comparison statistics per ${comparison.unit} (${comparison.method}, ${comparison.adjustment} adjustment)`}
      columns={columns}
      getRowKey={(row) => row.population}
      rows={comparison.rows}
    />
  );
}

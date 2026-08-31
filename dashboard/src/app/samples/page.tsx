"use client";

import { useEffect, useMemo, useState } from "react";

import { FilterBar } from "@/components/filters/FilterBar";
import { SamplesTable } from "@/components/samples/SamplesTable";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import type { DashboardBundle } from "@/lib/bundle.types";
import {
  EMPTY_FILTERS,
  filterSamples,
  parseFilters,
  serialiseFilters,
  type SampleFilters,
} from "@/lib/filters";
import {
  csvForLongRows,
  longRowsFor,
  sortSamples,
  type FrequencyRow,
  type SortDirection,
  type SortKey,
} from "@/lib/samples-view";
import { formatCount, formatPercentage, pluralise } from "@/lib/stats-format";

const PAGE_SIZE = 100;

const longColumns: DataColumn<FrequencyRow>[] = [
  { id: "sample", header: "sample", render: (row) => <code>{row.sample}</code> },
  {
    id: "total_count",
    header: "total_count",
    numeric: true,
    render: (row) => formatCount(row.total_count),
  },
  { id: "population", header: "population", render: (row) => <code>{row.population}</code> },
  { id: "count", header: "count", numeric: true, render: (row) => formatCount(row.count) },
  {
    id: "percentage",
    header: "percentage",
    numeric: true,
    render: (row) => formatPercentage(row.percentage),
  },
];

function downloadCsv(content: string, filename: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function SamplesWorkspace({ bundle }: { bundle: DashboardBundle }) {
  const [filters, setFilters] = useState<SampleFilters>(EMPTY_FILTERS);
  const [view, setView] = useState<"wide" | "long">("wide");
  const [sortKey, setSortKey] = useState<SortKey>("sample");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [visible, setVisible] = useState(PAGE_SIZE);

  useEffect(() => {
    // The static export prerenders without a query string, so the shareable
    // filter state can only be read after hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFilters(parseFilters(new URLSearchParams(window.location.search)));
  }, []);

  useEffect(() => {
    const query = serialiseFilters(filters).toString();
    const url = query ? `${window.location.pathname}?${query}` : window.location.pathname;
    window.history.replaceState(null, "", url);
  }, [filters]);

  const updateFilters = (next: SampleFilters) => {
    setFilters(next);
    setVisible(PAGE_SIZE);
  };

  const filtered = useMemo(() => filterSamples(bundle.samples, filters), [bundle.samples, filters]);
  const sorted = useMemo(
    () => sortSamples(filtered, sortKey, sortDirection),
    [filtered, sortKey, sortDirection],
  );
  const longRows = useMemo(
    () => longRowsFor(bundle.frequencies_long, sorted),
    [bundle.frequencies_long, sorted],
  );

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const totalRows = view === "wide" ? sorted.length : longRows.length;

  return (
    <>
      <PageIntro title="Cell frequency by sample">
        <p>
          Every sample with its population composition. Filters combine across fields; the long view
          is the exact Part 2 table and is what the CSV download produces.
        </p>
      </PageIntro>
      <FilterBar filters={filters} onChange={updateFilters} samples={bundle.samples} />
      <div className="results-bar">
        <p aria-live="polite">
          {formatCount(filtered.length)} of {pluralise(bundle.meta.n_samples, "sample")} match
        </p>
        <div className="results-actions">
          <button
            aria-pressed={view === "wide"}
            className="view-toggle"
            onClick={() => {
              setView("wide");
              setVisible(PAGE_SIZE);
            }}
            type="button"
          >
            Wide table
          </button>
          <button
            aria-pressed={view === "long"}
            className="view-toggle"
            onClick={() => {
              setView("long");
              setVisible(PAGE_SIZE);
            }}
            type="button"
          >
            Long table
          </button>
          <button
            disabled={longRows.length === 0}
            onClick={() => downloadCsv(csvForLongRows(longRows), "cell_frequencies.csv")}
            type="button"
          >
            Download CSV
          </button>
        </div>
      </div>
      {filtered.length === 0 ? (
        <div className="empty-state">
          <p>No samples match these filters.</p>
          <button onClick={() => updateFilters(EMPTY_FILTERS)} type="button">
            Clear filters
          </button>
        </div>
      ) : view === "wide" ? (
        <SamplesTable
          onSort={handleSort}
          populations={bundle.meta.populations}
          samples={sorted.slice(0, visible)}
          sortDirection={sortDirection}
          sortKey={sortKey}
        />
      ) : (
        <DataTable
          caption="Cell frequency long table (sample, total_count, population, count, percentage)"
          columns={longColumns}
          getRowKey={(row) => `${row.sample}-${row.population}`}
          rows={longRows.slice(0, visible)}
        />
      )}
      {visible < totalRows ? (
        <div className="show-more">
          <button onClick={() => setVisible(visible + PAGE_SIZE * 2)} type="button">
            Show more ({formatCount(totalRows - visible)} remaining)
          </button>
        </div>
      ) : null}
    </>
  );
}

export default function SamplesPage() {
  return <BundleContent>{(bundle) => <SamplesWorkspace bundle={bundle} />}</BundleContent>;
}

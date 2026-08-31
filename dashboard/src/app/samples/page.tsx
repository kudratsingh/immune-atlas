"use client";

import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import type { DashboardBundle } from "@/lib/bundle.types";
import { formatCount, formatPercentage } from "@/lib/stats-format";

type FrequencyRow = DashboardBundle["frequencies_long"][number];

const columns: DataColumn<FrequencyRow>[] = [
  { id: "sample", header: "Sample", render: (row) => <code>{row.sample}</code> },
  {
    id: "total",
    header: "Total count",
    numeric: true,
    render: (row) => formatCount(row.total_count),
  },
  { id: "population", header: "Population", render: (row) => row.population },
  { id: "count", header: "Count", numeric: true, render: (row) => formatCount(row.count) },
  {
    id: "percentage",
    header: "Percentage",
    numeric: true,
    render: (row) => formatPercentage(row.percentage),
  },
];

export default function SamplesPage() {
  return (
    <BundleContent>
      {(bundle) => (
        <>
          <PageIntro title="Cell frequency by sample">
            <p>
              The exact long-form table requested in Part 2, backed only by the analysis bundle.
            </p>
          </PageIntro>
          <CohortStrip
            steps={[
              { label: "All samples", count: bundle.meta.n_samples },
              { label: "Frequency rows", count: bundle.frequencies_long.length },
            ]}
          />
          <section className="content-section" aria-labelledby="frequency-preview">
            <div className="section-heading">
              <div>
                <h2 id="frequency-preview">Frequency table preview</h2>
                <p>
                  The full filtering, sorting, composition, and export workspace follows in the
                  Samples workstream.
                </p>
              </div>
            </div>
            <DataTable
              caption="First ten cell frequency rows"
              columns={columns}
              rows={bundle.frequencies_long.slice(0, 10)}
              getRowKey={(row) => `${row.sample}-${row.population}`}
            />
          </section>
        </>
      )}
    </BundleContent>
  );
}

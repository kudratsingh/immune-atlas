"use client";

import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import type { DashboardBundle } from "@/lib/bundle.types";

type Stage = DashboardBundle["run"]["stages"][number];
const columns: DataColumn<Stage>[] = [
  { id: "stage", header: "Stage", render: (stage) => <code>{stage.name}</code> },
  {
    id: "in",
    header: "Rows in",
    numeric: true,
    render: (stage) => stage.rows_in ?? "Not available",
  },
  {
    id: "out",
    header: "Rows out",
    numeric: true,
    render: (stage) => stage.rows_out ?? "Not available",
  },
  { id: "seconds", header: "Seconds", numeric: true, render: (stage) => stage.seconds.toFixed(2) },
];

export default function MethodsPage() {
  return (
    <BundleContent>
      {(bundle) => (
        <>
          <PageIntro title="Methods and provenance">
            <p>
              How frequencies are calculated, how response groups are compared, and where every
              displayed value came from.
            </p>
          </PageIntro>
          <section className="method-section">
            <h2>Frequencies</h2>
            <p>
              For each sample, a population count is divided by the total across all five
              populations and multiplied by 100.
            </p>
          </section>
          <section className="method-section">
            <h2>Response comparison</h2>
            <p>
              {bundle.response_analysis.by_sample.method} with{" "}
              {bundle.response_analysis.by_sample.adjustment} adjustment across five populations.
              Rank-biserial correlation reports effect size; positive values mean responders are
              higher.
            </p>
          </section>
          <section className="method-section">
            <h2>Provenance</h2>
            <dl className="definition-list">
              <div>
                <dt>Input checksum</dt>
                <dd>
                  <code>{bundle.run.source_sha256}</code>
                </dd>
              </div>
              <div>
                <dt>Pipeline version</dt>
                <dd>{bundle.run.pipeline_version}</dd>
              </div>
              <div>
                <dt>Python</dt>
                <dd>{bundle.run.python_version}</dd>
              </div>
            </dl>
            <DataTable
              caption="Pipeline stages"
              columns={columns}
              rows={bundle.run.stages}
              getRowKey={(stage) => stage.name}
            />
          </section>
        </>
      )}
    </BundleContent>
  );
}

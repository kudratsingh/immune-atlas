"use client";

import { PageIntro } from "@/components/layout/PageIntro";
import { SchemaDiagram } from "@/components/methods/SchemaDiagram";
import { BundleContent } from "@/components/states/BundleContent";
import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import type { DashboardBundle } from "@/lib/bundle.types";
import { formatCount } from "@/lib/stats-format";

const REPO_URL = "https://github.com/kudratsingh/immune-atlas/blob/main";

type Stage = DashboardBundle["run"]["stages"][number];
const stageColumns: DataColumn<Stage>[] = [
  { id: "stage", header: "Stage", render: (stage) => <code>{stage.name}</code> },
  {
    id: "in",
    header: "Rows in",
    numeric: true,
    render: (stage) => (stage.rows_in === null ? "Not applicable" : formatCount(stage.rows_in)),
  },
  {
    id: "out",
    header: "Rows out",
    numeric: true,
    render: (stage) => (stage.rows_out === null ? "Not applicable" : formatCount(stage.rows_out)),
  },
];

const TABLE_SENTENCES: [string, string][] = [
  ["projects", "One row per study; subjects reference it."],
  ["subjects", "Everything constant for a person, including the subject-level response label."],
  ["samples", "One row per drawn sample: its type and day, keyed to a subject."],
  ["cell_populations", "The five measured populations with display names and a fixed order."],
  ["cell_counts", "One count per sample and population; frequencies are computed from these."],
];

export default function MethodsPage() {
  return (
    <BundleContent>
      {(bundle) => {
        const versions = Object.entries(bundle.run.library_versions);
        return (
          <>
            <PageIntro title="Methods and provenance">
              <p>
                How frequencies are calculated, how response groups are compared, and where every
                displayed value came from.
              </p>
            </PageIntro>
            <section className="method-section">
              <h2>Data model</h2>
              <SchemaDiagram />
              <dl className="definition-list">
                {TABLE_SENTENCES.map(([table, sentence]) => (
                  <div key={table}>
                    <dt>
                      <code>{table}</code>
                    </dt>
                    <dd>{sentence}</dd>
                  </div>
                ))}
              </dl>
            </section>
            <section className="method-section">
              <h2>Frequencies</h2>
              <p>
                For each sample, a population count is divided by the total across all five
                populations and multiplied by 100. The percentages therefore sum to 100 for every
                sample, and the Samples page verifies that per row.
              </p>
            </section>
            <section className="method-section">
              <h2>Response comparison</h2>
              <p>
                Two-sided {bundle.response_analysis.by_sample.method} on per-sample relative
                frequencies, chosen because the count distributions are right-skewed with outliers,
                so a rank-based test needs no normality assumption. Effect size is the rank-biserial
                correlation (positive means responders are higher), reported with medians and IQRs
                so magnitude is visible alongside significance.{" "}
                {bundle.response_analysis.by_sample.adjustment} controls the false-discovery rate
                across the five populations tested.
              </p>
              <p>
                Response is a subject-level label while each subject contributes one sample per time
                point, so per-sample tests overstate independence. Two companions address this: a
                per-subject sensitivity analysis that averages each subject&apos;s samples into one
                value, and a time-stratified view that runs the test within each day — because a
                marker that separates groups only after treatment starts is a response indicator,
                not a baseline predictor.
              </p>
            </section>
            <section className="method-section">
              <h2>Provenance</h2>
              <dl className="definition-list">
                <div>
                  <dt>Input checksum (SHA-256)</dt>
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
                {versions.map(([library, version]) => (
                  <div key={library}>
                    <dt>{library}</dt>
                    <dd>{version}</dd>
                  </div>
                ))}
              </dl>
              <DataTable
                caption="Pipeline stages and row counts"
                columns={stageColumns}
                rows={bundle.run.stages}
                getRowKey={(stage) => stage.name}
              />
              <p className="method-footnote">
                This bundle is byte-reproducible, so it carries no wall-clock values; per-stage
                timings for the recorded run live in{" "}
                <a href={`${REPO_URL}/outputs/pipeline_run.json`}>outputs/pipeline_run.json</a>.
                {bundle.run.warnings.length === 0
                  ? " The run completed with no warnings."
                  : ` Warnings: ${bundle.run.warnings.join("; ")}`}
              </p>
            </section>
            <section className="method-section">
              <h2>Source</h2>
              <ul className="source-links">
                <li>
                  <a href={`${REPO_URL}/immune_atlas/db/schema.sql`}>The schema as executed</a>
                </li>
                <li>
                  <a href={`${REPO_URL}/immune_atlas/analysis/response.py`}>
                    The statistical tests as implemented
                  </a>
                </li>
                <li>
                  <a href={`${REPO_URL}/docs/adr/0002-response-comparison-statistics.md`}>
                    Why these tests were chosen
                  </a>
                </li>
                <li>
                  <a href={`${REPO_URL}/README.md`}>The repository README</a>
                </li>
              </ul>
            </section>
          </>
        );
      }}
    </BundleContent>
  );
}

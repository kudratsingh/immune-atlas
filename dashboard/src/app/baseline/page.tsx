"use client";

import Link from "next/link";
import { useState } from "react";

import { DistributionBars } from "@/components/charts/DistributionBars";
import { SmallMultiples } from "@/components/charts/SmallMultiples";
import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import { Pagination } from "@/components/tables/Pagination";
import { baselineCsv, baselineSampleRows } from "@/lib/baseline-view";
import type { BundleSample } from "@/lib/filters";
import { formatCount, pluralise } from "@/lib/stats-format";

const sampleColumns: DataColumn<BundleSample>[] = [
  { id: "sample", header: "Sample", render: (row) => <code>{row.sample}</code> },
  { id: "subject", header: "Subject", render: (row) => <code>{row.subject}</code> },
  { id: "project", header: "Project", render: (row) => row.project },
  { id: "age", header: "Age", numeric: true, render: (row) => row.age },
  { id: "sex", header: "Sex", render: (row) => row.sex },
  {
    id: "response",
    header: "Response",
    render: (row) => (row.response === "yes" ? "responder" : "non-responder"),
  },
  {
    id: "total",
    header: "Total count",
    numeric: true,
    render: (row) => formatCount(row.total_count),
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

const LIST_PAGE_SIZE = 50;

function BaselineSampleList({ rows }: { rows: BundleSample[] }) {
  const [page, setPage] = useState(1);
  const start = (page - 1) * LIST_PAGE_SIZE;
  return (
    <>
      <DataTable
        caption={`Baseline cohort samples (${formatCount(rows.length)})`}
        columns={sampleColumns}
        getRowKey={(row) => row.sample}
        rows={rows.slice(start, start + LIST_PAGE_SIZE)}
      />
      <Pagination
        label="Baseline samples"
        onChange={setPage}
        page={page}
        pageSize={LIST_PAGE_SIZE}
        totalRows={rows.length}
      />
    </>
  );
}

export default function BaselinePage() {
  return (
    <BundleContent>
      {(bundle) => {
        const baseline = bundle.baseline_subset;
        const form = bundle.form_answer;
        const rows = baselineSampleRows(bundle);
        const cohortSamples = bundle.samples.filter(
          (sample) =>
            sample.condition === baseline.filter.condition &&
            sample.treatment === baseline.filter.treatment,
        );
        return (
          <>
            <PageIntro title="Baseline cohort">
              <p>
                The Part 4 cohort: melanoma patients on miraclib, PBMC samples drawn at day 0. One
                sample per subject here, so the sample and subject counts coincide by construction,
                not by assumption.
              </p>
            </PageIntro>
            <CohortStrip
              steps={[
                { label: "All samples", count: bundle.meta.n_samples },
                {
                  label: baseline.filter.condition,
                  count: bundle.samples.filter(
                    (sample) => sample.condition === baseline.filter.condition,
                  ).length,
                },
                { label: baseline.filter.treatment, count: cohortSamples.length },
                {
                  label: baseline.filter.sample_type,
                  count: cohortSamples.filter(
                    (sample) => sample.sample_type === baseline.filter.sample_type,
                  ).length,
                },
                {
                  label: `Day ${baseline.filter.time ?? 0}`,
                  count: baseline.n_samples,
                  unit: `${baseline.n_subjects} subjects`,
                },
              ]}
            />
            <p className="cohort-groups">
              <Link
                href={`/samples/?condition=${baseline.filter.condition}&treatment=${baseline.filter.treatment}&sample_type=${baseline.filter.sample_type}&time=${baseline.filter.time ?? 0}`}
              >
                Open these samples in Samples
              </Link>
            </p>
            <SmallMultiples label="Baseline cohort breakdowns">
              <DistributionBars
                title="By project"
                unit="Samples"
                data={baseline.by_project.map((row) => ({
                  label: row.project,
                  value: row.n_samples,
                }))}
              />
              <DistributionBars
                title="By response"
                unit="Subjects"
                data={baseline.by_response.map((row) => ({
                  label: row.response === "yes" ? "Responders" : "Non-responders",
                  value: row.n_subjects,
                }))}
              />
              <DistributionBars
                title="By sex"
                unit="Subjects"
                data={baseline.by_sex.map((row) => ({ label: row.sex, value: row.n_subjects }))}
              />
            </SmallMultiples>
            <p className="inline-caveat">
              Projects are counted in samples; response and sex are counted in distinct subjects. At
              baseline the two coincide because each subject contributes exactly one sample.
            </p>
            <aside className="form-aside" aria-labelledby="form-question">
              <h2 id="form-question">A different filter: the assignment&apos;s form question</h2>
              <p>{form.question}</p>
              <p>
                Filter: {form.filter.condition}, {form.filter.sex === "M" ? "male" : "female"},{" "}
                {form.filter.response === "yes" ? "responders" : "non-responders"}, day{" "}
                {form.filter.time} — all sample types and treatments, so this is not the Part 4
                cohort above.
              </p>
              <p className="form-answer">
                Across {pluralise(form.n_samples, "sample")}, the mean B-cell count is{" "}
                <strong>
                  {form.mean_b_cell.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </strong>
                .
              </p>
            </aside>
            <section className="content-section" aria-labelledby="baseline-samples">
              <div className="section-heading">
                <div>
                  <h2 id="baseline-samples">Sample list</h2>
                  <p>Every baseline sample with its subject metadata.</p>
                </div>
                <button
                  className="button-primary"
                  onClick={() => downloadCsv(baselineCsv(rows), "baseline_subset.csv")}
                  type="button"
                >
                  Download CSV
                </button>
              </div>
              <BaselineSampleList rows={rows} />
            </section>
          </>
        );
      }}
    </BundleContent>
  );
}

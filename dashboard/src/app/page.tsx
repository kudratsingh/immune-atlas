"use client";

import Link from "next/link";

import { CohortStrip } from "@/components/layout/CohortStrip";
import { HeroMotif } from "@/components/layout/HeroMotif";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import { DataTable, type DataColumn } from "@/components/tables/DataTable";
import {
  conditionTreatmentSubjects,
  sampleTypeTimeCounts,
  type SampleTypeTimeCell,
  type SubjectCountCell,
} from "@/lib/samples-view";
import { formatCount } from "@/lib/stats-format";

const structureColumns: DataColumn<SubjectCountCell>[] = [
  { id: "condition", header: "Condition", render: (row) => row.condition },
  { id: "treatment", header: "Treatment", render: (row) => row.treatment },
  { id: "subjects", header: "Subjects", numeric: true, render: (row) => formatCount(row.subjects) },
];

const typeTimeColumns: DataColumn<SampleTypeTimeCell>[] = [
  { id: "sample_type", header: "Sample type", render: (row) => row.sampleType },
  { id: "time", header: "Day", numeric: true, render: (row) => row.time },
  { id: "samples", header: "Samples", numeric: true, render: (row) => formatCount(row.samples) },
];

export default function OverviewPage() {
  return (
    <BundleContent>
      {(bundle) => (
        <>
          <PageIntro
            motif={<HeroMotif />}
            title="Immune cell populations across a clinical trial dataset"
          >
            <p>
              Explore cell composition, treatment response, and the baseline cohort from one
              reproducible analysis bundle.
            </p>
          </PageIntro>
          <CohortStrip
            title="Dataset at a glance"
            steps={[
              { label: "Projects", count: bundle.meta.n_projects },
              { label: "Subjects", count: bundle.meta.n_subjects },
              { label: "Samples", count: bundle.meta.n_samples },
              { label: "Populations", count: bundle.meta.populations.length },
            ]}
          />
          <section className="content-section" aria-labelledby="study-structure">
            <h2 id="study-structure">Study structure</h2>
            <div className="study-grid">
              <div>
                <h3>Condition and treatment (subjects)</h3>
                <DataTable
                  caption="Distinct subjects for each condition and treatment"
                  columns={structureColumns}
                  getRowKey={(row) => `${row.condition}-${row.treatment}`}
                  rows={conditionTreatmentSubjects(bundle.samples)}
                />
              </div>
              <div>
                <h3>Sample type and time point (samples)</h3>
                <DataTable
                  caption="Samples for each sample type and time point"
                  columns={typeTimeColumns}
                  getRowKey={(row) => `${row.sampleType}-${row.time}`}
                  rows={sampleTypeTimeCounts(bundle.samples)}
                />
              </div>
            </div>
            <p className="structure-footnote">
              Populations measured in every sample:{" "}
              {bundle.meta.populations.map((population) => population.display_name).join(", ")} —{" "}
              {formatCount(bundle.frequencies_long.length)} frequency rows in total.
            </p>
          </section>
          <section className="content-section questions" aria-labelledby="three-questions">
            <h2 id="three-questions">Three questions</h2>
            <ol>
              <li>
                <div className="question-copy">
                  <Link href="/samples/">
                    What is the frequency of each population in each sample?
                  </Link>
                  <span>Filter, sort, and export every composition.</span>
                </div>
                <p className="question-stat">
                  <strong>{formatCount(bundle.frequencies_long.length)}</strong>
                  <small>frequency rows</small>
                </p>
              </li>
              <li>
                <div className="question-copy">
                  <Link href="/response/">
                    Do responders differ from non-responders on miraclib?
                  </Link>
                  <span>Statistics and observed distributions, per sample and per subject.</span>
                </div>
                <p className="question-stat">
                  <strong>
                    {formatCount(
                      bundle.response_analysis.n.samples_yes +
                        bundle.response_analysis.n.samples_no,
                    )}
                  </strong>
                  <small>PBMC samples</small>
                </p>
              </li>
              <li>
                <div className="question-copy">
                  <Link href="/baseline/">Who is in the baseline miraclib cohort?</Link>
                  <span>Project, response, and sex breakdowns at day 0.</span>
                </div>
                <p className="question-stat">
                  <strong>{formatCount(bundle.baseline_subset.n_subjects)}</strong>
                  <small>subjects</small>
                </p>
              </li>
            </ol>
          </section>
          <p className="provenance-line">
            Source: <code>{bundle.meta.source_file}</code> (checksum{" "}
            {bundle.meta.source_sha256.slice(0, 12)}…)
          </p>
        </>
      )}
    </BundleContent>
  );
}

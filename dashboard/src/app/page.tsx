"use client";

import Link from "next/link";

import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import { formatCount, pluralise } from "@/lib/stats-format";

export default function OverviewPage() {
  return (
    <BundleContent>
      {(bundle) => (
        <>
          <PageIntro title="Immune cell populations across a clinical trial dataset">
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
                <h3>Clinical dimensions</h3>
                <dl className="definition-list">
                  <div>
                    <dt>Conditions</dt>
                    <dd>{bundle.meta.conditions.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Treatments</dt>
                    <dd>{bundle.meta.treatments.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Sample types</dt>
                    <dd>{bundle.meta.sample_types.join(", ")}</dd>
                  </div>
                </dl>
              </div>
              <div>
                <h3>Measurement dimensions</h3>
                <dl className="definition-list">
                  <div>
                    <dt>Time points</dt>
                    <dd>{bundle.meta.time_points.map((time) => `day ${time}`).join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Cell populations</dt>
                    <dd>
                      {bundle.meta.populations
                        .map((population) => population.display_name)
                        .join(", ")}
                    </dd>
                  </div>
                  <div>
                    <dt>Frequency rows</dt>
                    <dd>{formatCount(bundle.frequencies_long.length)}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </section>
          <section className="content-section questions" aria-labelledby="three-questions">
            <h2 id="three-questions">Three questions</h2>
            <ol>
              <li>
                <Link href="/samples/">
                  What is the frequency of each population in each sample?
                </Link>
                <span>{pluralise(bundle.meta.n_samples, "sample")} available</span>
              </li>
              <li>
                <Link href="/response/">Do responders differ from non-responders on miraclib?</Link>
                <span>Statistics and observed distributions</span>
              </li>
              <li>
                <Link href="/baseline/">Who is in the baseline miraclib cohort?</Link>
                <span>Project, response, and sex breakdowns</span>
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

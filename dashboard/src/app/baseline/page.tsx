"use client";

import { DistributionBars } from "@/components/charts/DistributionBars";
import { SmallMultiples } from "@/components/charts/SmallMultiples";
import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";

export default function BaselinePage() {
  return (
    <BundleContent>
      {(bundle) => {
        const baseline = bundle.baseline_subset;
        return (
          <>
            <PageIntro title="Baseline cohort">
              <p>Melanoma PBMC samples at day 0 from patients treated with miraclib.</p>
            </PageIntro>
            <CohortStrip
              steps={[
                {
                  label: baseline.filter.condition,
                  count: bundle.samples.filter(
                    (sample) => sample.condition === baseline.filter.condition,
                  ).length,
                },
                {
                  label: baseline.filter.treatment,
                  count: bundle.samples.filter(
                    (sample) =>
                      sample.condition === baseline.filter.condition &&
                      sample.treatment === baseline.filter.treatment,
                  ).length,
                },
                {
                  label: baseline.filter.sample_type,
                  count: bundle.samples.filter((sample) =>
                    baseline.sample_ids.includes(sample.sample),
                  ).length,
                },
                {
                  label: `Day ${baseline.filter.time ?? 0}`,
                  count: baseline.n_samples,
                  unit: `${baseline.n_subjects} subjects`,
                },
              ]}
            />
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
          </>
        );
      }}
    </BundleContent>
  );
}

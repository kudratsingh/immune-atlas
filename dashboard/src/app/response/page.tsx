"use client";

import { BoxPlot, type BoxPlotPoint } from "@/components/charts/BoxPlot";
import { SmallMultiples } from "@/components/charts/SmallMultiples";
import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { BundleContent } from "@/components/states/BundleContent";
import type { DashboardBundle } from "@/lib/bundle.types";

function pointsFor(bundle: DashboardBundle, population: string): BoxPlotPoint[] {
  return bundle.response_analysis.distributions
    .filter((distribution) => distribution.population === population)
    .flatMap((distribution) =>
      distribution.points.map((point) => ({ ...point, response: distribution.response })),
    );
}

export default function ResponsePage() {
  return (
    <BundleContent>
      {(bundle) => {
        const response = bundle.response_analysis;
        const nSamples = response.n.samples_yes + response.n.samples_no;
        return (
          <>
            <PageIntro title="Response analysis">
              <p>
                Responder and non-responder distributions for melanoma patients receiving miraclib.
              </p>
            </PageIntro>
            <CohortStrip
              steps={[
                { label: "All samples", count: bundle.meta.n_samples },
                {
                  label: response.cohort.condition,
                  count: bundle.samples.filter(
                    (sample) => sample.condition === response.cohort.condition,
                  ).length,
                },
                {
                  label: response.cohort.treatment,
                  count: bundle.samples.filter(
                    (sample) =>
                      sample.condition === response.cohort.condition &&
                      sample.treatment === response.cohort.treatment,
                  ).length,
                },
                {
                  label: response.cohort.sample_type,
                  count: nSamples,
                  unit: `${response.by_sample.n_subjects} subjects`,
                },
              ]}
            />
            <div className="group-legend" aria-label="Response group legend">
              <span className="responder-swatch" /> Responders{" "}
              <span className="non-responder-swatch" /> Non-responders
            </div>
            <SmallMultiples label="Cell population box plots">
              {bundle.meta.populations.map((population) => (
                <BoxPlot
                  key={population.name}
                  title={population.display_name}
                  points={pointsFor(bundle, population.name)}
                />
              ))}
            </SmallMultiples>
            <p className="inline-caveat">
              Each point is a sample. The statistical view includes a per-subject sensitivity
              analysis because subjects contribute repeated time points.
            </p>
          </>
        );
      }}
    </BundleContent>
  );
}

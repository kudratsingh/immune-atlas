"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { BoxPlot } from "@/components/charts/BoxPlot";
import { SmallMultiples } from "@/components/charts/SmallMultiples";
import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { StatsTable } from "@/components/response/StatsTable";
import { BundleContent } from "@/components/states/BundleContent";
import type { DashboardBundle } from "@/lib/bundle.types";
import {
  activeComparison,
  availableTimes,
  displayNameLookup,
  findingText,
  pointsFor,
  statsCsv,
  type TimeMode,
  type UnitMode,
} from "@/lib/response-view";
import { formatPValue } from "@/lib/stats-format";

function downloadCsv(content: string, filename: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function svgToImage(svg: SVGSVGElement): Promise<HTMLImageElement> {
  const markup = new XMLSerializer().serializeToString(svg);
  const url = URL.createObjectURL(new Blob([markup], { type: "image/svg+xml" }));
  try {
    return await new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error("plot image failed to load"));
      image.src = url;
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function downloadPlotsPng() {
  const svgs = [...document.querySelectorAll<SVGSVGElement>(".small-multiples svg")];
  if (svgs.length === 0) return;
  const scale = 2;
  const width = 360;
  const height = 300;
  const canvas = document.createElement("canvas");
  canvas.width = width * svgs.length * scale;
  canvas.height = height * scale;
  const context = canvas.getContext("2d");
  if (!context) return;
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  const images = await Promise.all(svgs.map((svg) => svgToImage(svg)));
  images.forEach((image, index) => {
    context.drawImage(image, index * width * scale, 0, width * scale, height * scale);
  });
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "response_boxplots.png";
    anchor.click();
    URL.revokeObjectURL(url);
  });
}

function ResponseWorkspace({ bundle }: { bundle: DashboardBundle }) {
  const [unit, setUnit] = useState<UnitMode>("sample");
  const [time, setTime] = useState<TimeMode>("all");

  const analysis = bundle.response_analysis;
  const names = useMemo(() => displayNameLookup(bundle.meta.populations), [bundle]);
  const comparison = activeComparison(analysis, unit, time);
  const nSamples = analysis.n.samples_yes + analysis.n.samples_no;
  const statsByPopulation = new Map(comparison.rows.map((row) => [row.population, row]));

  const melanomaSamples = bundle.samples.filter(
    (sample) => sample.condition === analysis.cohort.condition,
  );
  const treatedSamples = melanomaSamples.filter(
    (sample) => sample.treatment === analysis.cohort.treatment,
  );

  return (
    <>
      <PageIntro title="Response analysis">
        <p>
          Do responders differ from non-responders in immune cell composition? Every claim below is
          generated from the statistics in the analysis bundle.
        </p>
      </PageIntro>
      <CohortStrip
        steps={[
          { label: "All samples", count: bundle.meta.n_samples },
          { label: analysis.cohort.condition, count: melanomaSamples.length },
          { label: analysis.cohort.treatment, count: treatedSamples.length },
          {
            label: analysis.cohort.sample_type,
            count: nSamples,
            unit: `${analysis.by_sample.n_subjects} subjects`,
          },
        ]}
      />
      <p className="cohort-groups">
        Responders: {analysis.n.subjects_yes} subjects / {analysis.n.samples_yes} samples.
        Non-responders: {analysis.n.subjects_no} subjects / {analysis.n.samples_no} samples.{" "}
        <Link
          href={`/samples/?condition=${analysis.cohort.condition}&treatment=${analysis.cohort.treatment}&sample_type=${analysis.cohort.sample_type}`}
        >
          Open these samples in Samples
        </Link>
      </p>
      <div className="results-bar">
        <div className="toggle-group" role="group" aria-label="Unit of analysis">
          <span>Unit:</span>
          <button
            aria-pressed={unit === "sample"}
            className="view-toggle"
            onClick={() => setUnit("sample")}
            type="button"
          >
            Per sample
          </button>
          <button
            aria-pressed={unit === "subject"}
            className="view-toggle"
            disabled={time !== "all"}
            onClick={() => setUnit("subject")}
            type="button"
          >
            Per subject
          </button>
        </div>
        <div className="toggle-group" role="group" aria-label="Time point">
          <span>Time point:</span>
          <button
            aria-pressed={time === "all"}
            className="view-toggle"
            onClick={() => setTime("all")}
            type="button"
          >
            All
          </button>
          {availableTimes(analysis).map((value) => (
            <button
              aria-pressed={time === value}
              className="view-toggle"
              key={value}
              onClick={() => {
                setTime(value);
                setUnit("sample");
              }}
              type="button"
            >
              Day {value}
            </button>
          ))}
        </div>
        <button
          onClick={() =>
            downloadCsv(
              statsCsv(comparison),
              `response_comparison_${comparison.unit}${time === "all" ? "" : `_day${time}`}.csv`,
            )
          }
          type="button"
        >
          Download statistics CSV
        </button>
        <button onClick={() => void downloadPlotsPng()} type="button">
          Download plots PNG
        </button>
      </div>
      <div className="group-legend" aria-label="Response group legend">
        <span className="responder-swatch" /> Responders <span className="non-responder-swatch" />{" "}
        Non-responders
      </div>
      <SmallMultiples label="Cell population box plots">
        {bundle.meta.populations.map((population) => {
          const row = statsByPopulation.get(population.name);
          return (
            <div className="chart-with-stats" key={population.name}>
              <BoxPlot
                title={population.display_name}
                points={pointsFor(analysis, population.name, time)}
              />
              {row ? (
                <p className="chart-stat-line">
                  p = {formatPValue(row.p_value)}, q = {formatPValue(row.q_value)}
                </p>
              ) : null}
            </div>
          );
        })}
      </SmallMultiples>
      <p className="inline-caveat">
        Each point is one sample. Subjects contribute one sample per time point, so the per-subject
        toggle averages a subject&apos;s samples before testing; the time-point facet tests each day
        separately.
      </p>
      <section className="content-section" aria-labelledby="finding">
        <h2 id="finding">Finding</h2>
        <p className="finding-block">{findingText(analysis, names)}</p>
      </section>
      <section className="content-section" aria-labelledby="statistics">
        <h2 id="statistics">Statistics</h2>
        <StatsTable comparison={comparison} names={names} />
        <p className="method-footnote">
          Two-sided {comparison.method} on relative frequencies with {comparison.adjustment}{" "}
          adjustment across {comparison.rows.length} populations; rank-biserial correlation as the
          effect size. Full method details are on the <Link href="/methods/">Methods page</Link>.
        </p>
      </section>
    </>
  );
}

export default function ResponsePage() {
  return <BundleContent>{(bundle) => <ResponseWorkspace bundle={bundle} />}</BundleContent>;
}

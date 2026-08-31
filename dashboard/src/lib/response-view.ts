import type { BoxPlotPoint } from "@/components/charts/BoxPlot";

import type { DashboardBundle } from "./bundle.types";
import { formatPValue } from "./stats-format";

export type ResponseAnalysis = DashboardBundle["response_analysis"];
export type Comparison = ResponseAnalysis["by_sample"];
export type ComparisonRow = Comparison["rows"][number];
export type UnitMode = "sample" | "subject";
export type TimeMode = "all" | number;

export function availableTimes(analysis: ResponseAnalysis): number[] {
  return analysis.by_time.map((entry) => entry.time);
}

export function activeComparison(
  analysis: ResponseAnalysis,
  unit: UnitMode,
  time: TimeMode,
): Comparison {
  if (time !== "all") {
    const entry = analysis.by_time.find((candidate) => candidate.time === time);
    if (entry) return entry.comparison;
  }
  return unit === "subject" ? analysis.by_subject : analysis.by_sample;
}

export function pointsFor(
  analysis: ResponseAnalysis,
  population: string,
  time: TimeMode,
): BoxPlotPoint[] {
  return analysis.distributions
    .filter((distribution) => distribution.population === population)
    .flatMap((distribution) =>
      distribution.points
        .filter((point) => time === "all" || point.time === time)
        .map((point) => ({ ...point, response: distribution.response })),
    );
}

type NameLookup = ReadonlyMap<string, string>;

export function displayNameLookup(populations: DashboardBundle["meta"]["populations"]): NameLookup {
  return new Map(populations.map((population) => [population.name, population.display_name]));
}

function displayName(names: NameLookup, population: string): string {
  return names.get(population) ?? population;
}

function listNames(names: NameLookup, rows: ComparisonRow[]): string {
  const labels = rows.map((row) => displayName(names, row.population));
  if (labels.length <= 1) return labels.join("");
  return `${labels.slice(0, -1).join(", ")} and ${labels.at(-1)}`;
}

function rawHits(comparison: Comparison): ComparisonRow[] {
  return comparison.rows.filter((row) => row.p_value !== null && row.p_value < comparison.alpha);
}

function subjectSentence(analysis: ResponseAnalysis, names: NameLookup): string {
  const comparison = analysis.by_subject;
  if (comparison.rows.every((row) => row.p_value === null)) {
    return "The per-subject sensitivity analysis could not be computed for groups this small.";
  }
  const hits = rawHits(comparison);
  if (hits.length === 0) {
    return (
      "The per-subject sensitivity analysis, which averages each subject's samples into " +
      "one value, finds no population below the threshold."
    );
  }
  const listing = hits
    .map((row) => `${displayName(names, row.population)} at p = ${formatPValue(row.p_value)}`)
    .join(", ");
  return (
    "The per-subject sensitivity analysis, which averages each subject's samples into " +
    `one value, agrees: ${listing}.`
  );
}

function timeSentence(analysis: ResponseAnalysis, names: NameLookup): string {
  if (analysis.by_time.length === 0) return "";
  const parts: string[] = [];
  let baselineClear = false;
  for (const entry of analysis.by_time) {
    const hits = rawHits(entry.comparison);
    if (entry.time === 0 && hits.length === 0) {
      baselineClear = true;
      continue;
    }
    if (hits.length > 0) {
      const listing = hits
        .map((row) => `${displayName(names, row.population)} (p = ${formatPValue(row.p_value)})`)
        .join(" and ");
      parts.push(`${listing} at day ${entry.time}`);
    }
  }
  if (parts.length === 0) {
    return "Stratified by time point, no single day shows a difference on its own.";
  }
  const opening = baselineClear
    ? "Stratified by time point, no population differs at baseline; the separation appears in "
    : "Stratified by time point, differences appear in ";
  return `${opening}${parts.join(" and ")}.`;
}

export function findingText(analysis: ResponseAnalysis, names: NameLookup): string {
  const comparison = analysis.by_sample;
  const cohort = analysis.cohort;
  const nSamples = analysis.n.samples_yes + analysis.n.samples_no;
  const raw = rawHits(comparison);
  const adjusted = comparison.rows.filter((row) => row.significant_adjusted);
  const rawClause =
    raw.length === 0
      ? "no population differs"
      : `${listNames(names, raw)} ${raw.length === 1 ? "differs" : "differ"}`;
  const rawDetail =
    raw.length === 0 ? "" : ` (${raw.map((row) => `p = ${formatPValue(row.p_value)}`).join(", ")})`;
  const adjustedClause =
    adjusted.length === 0
      ? "none remains significant"
      : `${listNames(names, adjusted)} ${adjusted.length === 1 ? "remains" : "remain"} significant`;
  const adjustedDetail =
    raw.length === 0 ? "" : ` (${raw.map((row) => `q = ${formatPValue(row.q_value)}`).join(", ")})`;
  const sentences = [
    `Across ${nSamples.toLocaleString("en-US")} ${cohort.sample_type} samples from ` +
      `${comparison.n_subjects.toLocaleString("en-US")} ${cohort.condition} patients on ` +
      `${cohort.treatment}, ${rawClause} in relative frequency between responders and ` +
      `non-responders at p < ${comparison.alpha}${rawDetail} (${comparison.method}).`,
    `After ${comparison.adjustment} adjustment across ${comparison.rows.length} populations, ` +
      `${adjustedClause}${adjustedDetail}.`,
    subjectSentence(analysis, names),
    timeSentence(analysis, names),
  ];
  return sentences.filter(Boolean).join(" ");
}

export function statsCsv(comparison: Comparison): string {
  const header =
    "population,n_yes,n_no,median_yes,median_no,iqr_low_yes,iqr_high_yes,iqr_low_no," +
    "iqr_high_no,u_statistic,p_value,q_value,effect_size,welch_p,significant_adjusted";
  const cell = (value: number | null | undefined): string =>
    value === null || value === undefined ? "" : String(value);
  const lines = comparison.rows.map((row) =>
    [
      row.population,
      row.n_yes,
      row.n_no,
      cell(row.median_yes),
      cell(row.median_no),
      cell(row.iqr_yes?.[0]),
      cell(row.iqr_yes?.[1]),
      cell(row.iqr_no?.[0]),
      cell(row.iqr_no?.[1]),
      cell(row.u_statistic),
      cell(row.p_value),
      cell(row.q_value),
      cell(row.effect_size),
      cell(row.welch_p),
      row.significant_adjusted,
    ].join(","),
  );
  return `${[header, ...lines].join("\n")}\n`;
}

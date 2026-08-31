import type { DashboardBundle } from "./bundle.types";
import type { BundleSample } from "./filters";

export function baselineSampleRows(bundle: DashboardBundle): BundleSample[] {
  const wanted = new Set(bundle.baseline_subset.sample_ids);
  return bundle.samples.filter((sample) => wanted.has(sample.sample));
}

export function baselineCsv(rows: BundleSample[]): string {
  const header = "sample,subject,project,condition,age,sex,treatment,response";
  const lines = rows.map((row) =>
    [
      row.sample,
      row.subject,
      row.project,
      row.condition,
      row.age,
      row.sex,
      row.treatment,
      row.response ?? "",
    ].join(","),
  );
  return `${[header, ...lines].join("\n")}\n`;
}

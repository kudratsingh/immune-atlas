import { describe, expect, it } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import { baselineCsv, baselineSampleRows } from "@/lib/baseline-view";
import { validateBundle } from "@/lib/bundle";

const bundle = validateBundle(fixture);

describe("baselineSampleRows", () => {
  it("returns exactly the samples named by the baseline subset", () => {
    const rows = baselineSampleRows(bundle);
    expect(rows.map((row) => row.sample).sort()).toEqual(
      [...bundle.baseline_subset.sample_ids].sort(),
    );
    expect(rows).toHaveLength(bundle.baseline_subset.n_samples);
  });
});

describe("baselineCsv", () => {
  it("writes subject metadata columns with empty response for untreated", () => {
    const rows = baselineSampleRows(bundle);
    const csv = baselineCsv(rows);
    const lines = csv.trimEnd().split("\n");
    expect(lines[0]).toBe("sample,subject,project,condition,age,sex,treatment,response");
    expect(lines).toHaveLength(rows.length + 1);
    expect(csv.endsWith("\n")).toBe(true);
    const untreated = baselineCsv([{ ...rows[0], response: null }]);
    expect(untreated.trimEnd().split("\n")[1].endsWith(",")).toBe(true);
  });
});

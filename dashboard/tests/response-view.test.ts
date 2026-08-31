import { describe, expect, it } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import { validateBundle } from "@/lib/bundle";
import {
  activeComparison,
  availableTimes,
  displayNameLookup,
  findingText,
  pointsFor,
  statsCsv,
  type ResponseAnalysis,
} from "@/lib/response-view";

const bundle = validateBundle(fixture);
const analysis = bundle.response_analysis;
const names = displayNameLookup(bundle.meta.populations);

describe("activeComparison", () => {
  it("selects the per-sample, per-subject, and per-time comparisons", () => {
    expect(activeComparison(analysis, "sample", "all").unit).toBe("sample");
    expect(activeComparison(analysis, "subject", "all").unit).toBe("subject");
    const dayZero = activeComparison(analysis, "sample", 0);
    expect(dayZero).toBe(analysis.by_time[0].comparison);
  });

  it("lists the available time points in order", () => {
    expect(availableTimes(analysis)).toEqual([0, 7, 14]);
  });
});

describe("pointsFor", () => {
  it("returns tagged points for one population, optionally sliced by time", () => {
    const all = pointsFor(analysis, "cd4_t_cell", "all");
    expect(all.length).toBeGreaterThan(0);
    expect(new Set(all.map((point) => point.response))).toEqual(new Set(["yes", "no"]));
    const dayZero = pointsFor(analysis, "cd4_t_cell", 0);
    expect(dayZero.every((point) => point.time === 0)).toBe(true);
    expect(dayZero.length).toBeLessThan(all.length);
  });
});

describe("findingText", () => {
  it("reports a null result without inventing findings", () => {
    const text = findingText(analysis, names);
    expect(text).toContain("no population differs");
    expect(text).toContain("none remains significant");
    expect(text).toContain("could not be computed for groups this small");
    expect(text).not.toContain("undefined");
  });

  it("names the populations and thresholds when differences exist", () => {
    const rows = analysis.by_sample.rows.map((row) =>
      row.population === "cd4_t_cell"
        ? { ...row, p_value: 0.013, q_value: 0.067, significant_raw: true }
        : row,
    );
    const planted: ResponseAnalysis = {
      ...analysis,
      by_sample: { ...analysis.by_sample, rows },
      by_time: [
        { time: 0, comparison: { ...analysis.by_sample, rows: analysis.by_sample.rows } },
        { time: 7, comparison: { ...analysis.by_sample, rows } },
      ],
    };
    const text = findingText(planted, names);
    expect(text).toContain("CD4 T cells differs");
    expect(text).toContain("p = .013");
    expect(text).toContain("none remains significant (q = .067");
    expect(text).toContain("no population differs at baseline");
    expect(text).toContain("day 7");
  });
});

describe("statsCsv", () => {
  it("writes one row per population with empty cells for missing statistics", () => {
    const csv = statsCsv(analysis.by_subject);
    const lines = csv.trimEnd().split("\n");
    expect(lines[0].startsWith("population,n_yes,n_no")).toBe(true);
    expect(lines).toHaveLength(1 + analysis.by_subject.rows.length);
    expect(lines[1]).toContain(",,");
    expect(csv.endsWith("\n")).toBe(true);
  });

  it("carries the numeric statistics when they exist", () => {
    const csv = statsCsv(analysis.by_sample);
    expect(csv).toContain("cd4_t_cell");
    expect(csv).toContain("0.13203463203463203");
  });
});

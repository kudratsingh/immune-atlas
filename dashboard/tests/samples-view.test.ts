import { describe, expect, it } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import { validateBundle } from "@/lib/bundle";
import {
  compositionFor,
  conditionTreatmentSubjects,
  csvForLongRows,
  longRowsFor,
  percentageSum,
  sampleTypeTimeCounts,
  sortSamples,
  sumsToOneHundred,
} from "@/lib/samples-view";

const bundle = validateBundle(fixture);

describe("sortSamples", () => {
  it("sorts by string keys with a stable sample tie-break", () => {
    const sorted = sortSamples(bundle.samples, "subject", "asc");
    const subjects = sorted.map((sample) => sample.subject);
    expect([...subjects].sort((a, b) => a.localeCompare(b))).toEqual(subjects);
    expect(sortSamples(bundle.samples, "subject", "desc").map((s) => s.subject)).toEqual(
      [...subjects].reverse(),
    );
  });

  it("sorts numeric keys numerically", () => {
    const ascending = sortSamples(bundle.samples, "total_count", "asc");
    const totals = ascending.map((sample) => sample.total_count);
    expect([...totals].sort((a, b) => a - b)).toEqual(totals);
  });

  it("does not mutate its input", () => {
    const before = bundle.samples.map((sample) => sample.sample);
    sortSamples(bundle.samples, "total_count", "desc");
    expect(bundle.samples.map((sample) => sample.sample)).toEqual(before);
  });
});

describe("longRowsFor", () => {
  it("keeps exactly the frequency rows for the given samples", () => {
    const subset = bundle.samples.slice(0, 2);
    const rows = longRowsFor(bundle.frequencies_long, subset);
    expect(rows).toHaveLength(subset.length * bundle.meta.populations.length);
    expect(new Set(rows.map((row) => row.sample))).toEqual(
      new Set(subset.map((sample) => sample.sample)),
    );
  });
});

describe("csvForLongRows", () => {
  it("writes the exact Part 2 header and six-decimal percentages", () => {
    const csv = csvForLongRows(longRowsFor(bundle.frequencies_long, bundle.samples.slice(0, 1)));
    const lines = csv.trimEnd().split("\n");
    expect(lines[0]).toBe("sample,total_count,population,count,percentage");
    expect(lines).toHaveLength(1 + bundle.meta.populations.length);
    expect(lines[1]).toMatch(/,\d+\.\d{6}$/);
    expect(csv.endsWith("\n")).toBe(true);
  });
});

describe("composition helpers", () => {
  it("orders segments by population sort order with their percentages", () => {
    const segments = compositionFor(bundle.samples[0], bundle.meta.populations);
    expect(segments.map((segment) => segment.colourIndex)).toEqual([0, 1, 2, 3, 4]);
    expect(segments.map((segment) => segment.name)).toEqual(
      bundle.meta.populations.map((population) => population.name),
    );
  });

  it("confirms percentages sum to one hundred within tolerance", () => {
    for (const sample of bundle.samples) {
      expect(sumsToOneHundred(sample)).toBe(true);
      expect(percentageSum(sample)).toBeGreaterThan(99.9);
    }
    const broken = {
      ...bundle.samples[0],
      percentages: { ...bundle.samples[0].percentages, b_cell: 0 },
    };
    expect(sumsToOneHundred(broken)).toBe(false);
  });
});

describe("study structure counts", () => {
  it("counts distinct subjects per condition and treatment", () => {
    expect(conditionTreatmentSubjects(bundle.samples)).toEqual([
      { condition: "healthy", treatment: "none", subjects: 1 },
      { condition: "melanoma", treatment: "miraclib", subjects: 4 },
    ]);
  });

  it("counts samples per sample type and time point", () => {
    expect(sampleTypeTimeCounts(bundle.samples)).toEqual([
      { sampleType: "PBMC", time: 0, samples: 5 },
      { sampleType: "PBMC", time: 7, samples: 5 },
      { sampleType: "PBMC", time: 14, samples: 5 },
    ]);
  });
});

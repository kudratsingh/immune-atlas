import { describe, expect, it } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import { validateBundle } from "@/lib/bundle";
import {
  EMPTY_FILTERS,
  filterOptions,
  filterSamples,
  parseFilters,
  serialiseFilters,
} from "@/lib/filters";

const bundle = validateBundle(fixture);

describe("sample filters", () => {
  it("applies AND across fields and OR within a field", () => {
    const result = filterSamples(bundle.samples, {
      ...EMPTY_FILTERS,
      response: ["yes"],
      time: ["0", "7"],
    });
    expect(result).toHaveLength(4);
    expect(result.every((sample) => sample.response === "yes" && sample.time !== 14)).toBe(true);
  });

  it("matches sample and subject identifiers case-insensitively", () => {
    expect(filterSamples(bundle.samples, { ...EMPTY_FILTERS, search: "SAMPLE00024" })).toHaveLength(
      1,
    );
    expect(filterSamples(bundle.samples, { ...EMPTY_FILTERS, search: "SBJ008" })).toHaveLength(3);
  });

  it("returns naturally sorted distinct options", () => {
    expect(filterOptions(bundle.samples, "time")).toEqual(["0", "7", "14"]);
    expect(filterOptions(bundle.samples, "response")).toEqual(["no", "yes"]);
  });

  it("round-trips URL query parameters", () => {
    const params = new URLSearchParams("project=prj1&time=0&time=14&search=sbj008");
    const filters = parseFilters(params);
    expect(filters.project).toEqual(["prj1"]);
    expect(filters.time).toEqual(["0", "14"]);
    expect(serialiseFilters(filters).toString()).toBe("project=prj1&time=0&time=14&search=sbj008");
  });
});

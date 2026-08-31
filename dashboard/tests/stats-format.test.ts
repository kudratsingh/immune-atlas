import { describe, expect, it } from "vitest";

import {
  formatCount,
  formatEffectSize,
  formatPercentage,
  formatPValue,
  pluralise,
} from "@/lib/stats-format";

describe("statistics formatting", () => {
  it("formats human-readable counts and percentages", () => {
    expect(formatCount(10500)).toBe("10,500");
    expect(formatPercentage(12.3456)).toBe("12.35%");
    expect(formatPercentage(null)).toBe("Not available");
    expect(formatPercentage(Number.NaN)).toBe("Not available");
  });

  it("formats p-values without implying false precision", () => {
    expect(formatPValue(0.0004)).toBe("<0.001");
    expect(formatPValue(0.0132)).toBe(".013");
    expect(formatPValue(null)).toBe("Not available");
    expect(formatPValue(Number.POSITIVE_INFINITY)).toBe("Not available");
  });

  it("formats effect sizes and grammatical units", () => {
    expect(formatEffectSize(-0.456)).toBe("-0.46");
    expect(formatEffectSize(null)).toBe("Not available");
    expect(formatEffectSize(Number.NaN)).toBe("Not available");
    expect(pluralise(1, "sample")).toBe("1 sample");
    expect(pluralise(2, "person", "people")).toBe("2 people");
  });
});

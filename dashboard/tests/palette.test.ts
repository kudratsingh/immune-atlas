import { describe, expect, it } from "vitest";

import { PALETTE, populationColour, responseColour } from "@/lib/palette";

describe("dashboard palette", () => {
  it("uses fixed semantic response colours", () => {
    expect(responseColour("yes")).toBe(PALETTE.responder);
    expect(responseColour("no")).toBe(PALETTE.nonResponder);
  });

  it("clamps population colours to the five-colour ramp", () => {
    expect(populationColour(-1)).toBe(PALETTE.populations[0]);
    expect(populationColour(2)).toBe(PALETTE.populations[2]);
    expect(populationColour(99)).toBe(PALETTE.populations[4]);
  });
});

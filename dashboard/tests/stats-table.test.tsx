import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import { StatsTable } from "@/components/response/StatsTable";
import { validateBundle } from "@/lib/bundle";
import { displayNameLookup } from "@/lib/response-view";

const bundle = validateBundle(fixture);
const names = displayNameLookup(bundle.meta.populations);

describe("StatsTable", () => {
  it("shows display names, group sizes, and the significance verdict", () => {
    render(<StatsTable comparison={bundle.response_analysis.by_sample} names={names} />);
    expect(screen.getByText("CD4 T cells")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Responder samples" })).toBeInTheDocument();
    expect(screen.getAllByText("no")).toHaveLength(bundle.response_analysis.by_sample.rows.length);
  });

  it("labels subject-level comparisons and missing statistics honestly", () => {
    render(<StatsTable comparison={bundle.response_analysis.by_subject} names={names} />);
    expect(screen.getByRole("columnheader", { name: "Responder subjects" })).toBeInTheDocument();
    expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
  });
});

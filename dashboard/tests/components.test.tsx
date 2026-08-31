import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { BoxPlot, quantile, summarise, type BoxPlotPoint } from "@/components/charts/BoxPlot";
import { DistributionBars } from "@/components/charts/DistributionBars";
import { SmallMultiples } from "@/components/charts/SmallMultiples";
import { CohortStrip } from "@/components/layout/CohortStrip";
import { PageIntro } from "@/components/layout/PageIntro";
import { EmptyState, ErrorState, LoadingState } from "@/components/states/DataStates";

const points: BoxPlotPoint[] = [
  { sample: "s1", subject: "p1", time: 0, percentage: 10, response: "yes" },
  { sample: "s2", subject: "p2", time: 7, percentage: 12, response: "yes" },
  { sample: "s3", subject: "p3", time: 0, percentage: 8, response: "no" },
  { sample: "s4", subject: "p4", time: 7, percentage: 9, response: "no" },
];

describe("shared dashboard components", () => {
  it("renders the cohort definition as an ordered narrowing sequence", () => {
    render(
      <CohortStrip
        steps={[
          { label: "All samples", count: 10500 },
          { label: "PBMC", count: 1968, unit: "656 subjects" },
        ]}
      />,
    );
    expect(screen.getByRole("heading", { name: "Cohort" })).toBeInTheDocument();
    expect(screen.getByText("10,500")).toBeInTheDocument();
    expect(screen.getByText("656 subjects")).toBeInTheDocument();
  });

  it("encodes the narrowing cohort as taper connectors in funnel mode", () => {
    const { container } = render(
      <CohortStrip
        funnel
        steps={[
          { label: "All samples", count: 10500 },
          { label: "melanoma", count: 5175 },
          { label: "PBMC", count: 1968 },
        ]}
      />,
    );
    expect(container.querySelectorAll(".strip-connector")).toHaveLength(2);
  });

  it("renders headings and each state with direct recovery copy", async () => {
    const user = userEvent.setup();
    const clear = vi.fn();
    render(
      <>
        <PageIntro title="Trial overview">
          <p>Evidence</p>
        </PageIntro>
        <LoadingState />
        <ErrorState message="No data bundle found." />
        <EmptyState onClear={clear} />
      </>,
    );
    expect(screen.getByRole("heading", { name: "Trial overview" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("No data bundle found");
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(clear).toHaveBeenCalledOnce();
  });

  it("computes box summaries", () => {
    expect(quantile([0, 10], 0.25)).toBe(2.5);
    expect(quantile([], 0.5)).toBe(0);
    expect(summarise([1, 2, 3, 4])).toEqual({ q1: 1.75, median: 2.5, q3: 3.25, low: 1, high: 4 });
  });

  it("shows n per group and offers the exact data as a table", async () => {
    const user = userEvent.setup();
    render(<BoxPlot title="B cells" points={points} />);
    expect(screen.getByText("Responders n=2")).toBeInTheDocument();
    expect(screen.getByText("Non-responders n=2")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show as table" }));
    expect(screen.getByRole("table")).toHaveAccessibleName("B cells values by response group");
    expect(screen.getByText("s1")).toBeInTheDocument();
  });

  it("disables chart transitions for reduced-motion users", async () => {
    vi.spyOn(window, "matchMedia").mockReturnValue({
      matches: true,
      media: "(prefers-reduced-motion: reduce)",
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    });
    const { container } = render(<BoxPlot title="CD4 T cells" points={points} />);
    expect(container.querySelector("[data-reduced-motion='true']")).toBeInTheDocument();
  });

  it("renders direct-labelled bars and a table fallback inside small multiples", async () => {
    const user = userEvent.setup();
    render(
      <SmallMultiples label="Breakdowns">
        <DistributionBars
          title="By project"
          unit="Samples"
          data={[{ label: "prj1", value: 384 }]}
        />
      </SmallMultiples>,
    );
    expect(screen.getByRole("group", { name: "Breakdowns" })).toBeInTheDocument();
    expect(screen.getByText("384")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show as table" }));
    expect(screen.getByRole("table")).toHaveAccessibleName("By project, Samples");
  });
});

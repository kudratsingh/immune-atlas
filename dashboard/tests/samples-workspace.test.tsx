import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import { FilterBar } from "@/components/filters/FilterBar";
import { SamplesTable } from "@/components/samples/SamplesTable";
import { validateBundle } from "@/lib/bundle";
import { EMPTY_FILTERS } from "@/lib/filters";

const bundle = validateBundle(fixture);

describe("FilterBar", () => {
  it("toggles a value into and out of a field filter", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<FilterBar filters={EMPTY_FILTERS} onChange={onChange} samples={bundle.samples} />);

    await user.click(screen.getByText("Condition"));
    await user.click(screen.getByRole("checkbox", { name: "melanoma" }));
    expect(onChange).toHaveBeenLastCalledWith({ ...EMPTY_FILTERS, condition: ["melanoma"] });

    onChange.mockClear();
    render(
      <FilterBar
        filters={{ ...EMPTY_FILTERS, condition: ["melanoma"] }}
        onChange={onChange}
        samples={bundle.samples}
      />,
    );
    const bars = screen.getAllByRole("search");
    await user.click(within(bars[1]).getByText("Condition"));
    await user.click(within(bars[1]).getByRole("checkbox", { name: "melanoma" }));
    expect(onChange).toHaveBeenLastCalledWith({ ...EMPTY_FILTERS, condition: [] });
  });

  it("labels response and day values in the user's terms", async () => {
    const user = userEvent.setup();
    render(<FilterBar filters={EMPTY_FILTERS} onChange={vi.fn()} samples={bundle.samples} />);
    await user.click(screen.getByText("Response"));
    expect(screen.getByRole("checkbox", { name: "Responders" })).toBeInTheDocument();
    await user.click(screen.getByText("Day"));
    expect(screen.getByRole("checkbox", { name: "day 0" })).toBeInTheDocument();
  });

  it("clears every filter and reports the search text", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <FilterBar
        filters={{ ...EMPTY_FILTERS, sex: ["M"], search: "sbj" }}
        onChange={onChange}
        samples={bundle.samples}
      />,
    );
    await user.type(screen.getByRole("searchbox"), "0");
    expect(onChange).toHaveBeenLastCalledWith({ ...EMPTY_FILTERS, sex: ["M"], search: "sbj0" });
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(onChange).toHaveBeenLastCalledWith(EMPTY_FILTERS);
  });
});

describe("SamplesTable", () => {
  it("marks the active sort column and requests new sorts", async () => {
    const user = userEvent.setup();
    const onSort = vi.fn();
    render(
      <SamplesTable
        onSort={onSort}
        populations={bundle.meta.populations}
        samples={bundle.samples}
        sortDirection="asc"
        sortKey="sample"
      />,
    );
    expect(screen.getByRole("columnheader", { name: /Sample/ })).toHaveAttribute(
      "aria-sort",
      "ascending",
    );
    await user.click(screen.getByRole("button", { name: /Total count/ }));
    expect(onSort).toHaveBeenCalledWith("total_count");
  });

  it("renders a composition bar and expandable percentages for each sample", async () => {
    const user = userEvent.setup();
    render(
      <SamplesTable
        onSort={vi.fn()}
        populations={bundle.meta.populations}
        samples={bundle.samples.slice(0, 1)}
        sortDirection="asc"
        sortKey="sample"
      />,
    );
    expect(screen.getByRole("img", { name: /Composition:/ })).toBeInTheDocument();
    const toggle = screen.getByRole("button", { name: "Show percentages" });
    await user.click(toggle);
    expect(screen.getByRole("button", { name: "Hide percentages" })).toBeInTheDocument();
    expect(screen.getByText("B cells")).toBeInTheDocument();
  });

  it("labels untreated samples without coercing response to no", () => {
    const untreated = bundle.samples.filter((sample) => sample.response === null);
    render(
      <SamplesTable
        onSort={vi.fn()}
        populations={bundle.meta.populations}
        samples={untreated.slice(0, 1)}
        sortDirection="asc"
        sortKey="sample"
      />,
    );
    expect(screen.getByText("not applicable")).toBeInTheDocument();
  });
});

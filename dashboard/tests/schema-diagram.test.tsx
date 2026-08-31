import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SchemaDiagram } from "@/components/methods/SchemaDiagram";

describe("SchemaDiagram", () => {
  it("names every table and describes the relationships accessibly", () => {
    render(<SchemaDiagram />);
    const diagram = screen.getByRole("img", { name: /Database schema/ });
    expect(diagram).toBeInTheDocument();
    for (const table of ["projects", "subjects", "samples", "cell_counts", "cell_populations"]) {
      expect(screen.getByText(table)).toBeInTheDocument();
    }
  });
});

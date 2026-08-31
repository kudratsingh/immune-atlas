import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import fixture from "../../contracts/fixtures/bundle.small.json";
import {
  BUNDLE_URL,
  BundleProvider,
  loadBundle,
  resetBundleCache,
  useBundle,
  validateBundle,
} from "@/lib/bundle";

function StatusProbe() {
  const state = useBundle();
  return <div>{state.status === "ready" ? state.data.meta.n_samples : state.status}</div>;
}

describe("dashboard bundle", () => {
  beforeEach(() => {
    resetBundleCache();
    vi.restoreAllMocks();
  });

  it("loads and validates the supported bundle", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(fixture), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const bundle = await loadBundle(fetcher);
    expect(fetcher).toHaveBeenCalledWith(BUNDLE_URL, { cache: "no-store" });
    expect(bundle.meta.n_samples).toBe(15);
  });

  it("gives an actionable missing-bundle error", async () => {
    await expect(
      loadBundle(vi.fn().mockResolvedValue(new Response(null, { status: 404 }))),
    ).rejects.toThrow("Run `make pipeline`");
    await expect(
      loadBundle(vi.fn().mockResolvedValue(new Response(null, { status: 500 }))),
    ).rejects.toThrow("HTTP 500");
  });

  it("rejects malformed and incompatible bundles", async () => {
    expect(() => validateBundle(null)).toThrow("not a JSON object");
    expect(() => validateBundle({ ...fixture, schema_version: "2.0" })).toThrow("expected 1.0");
    expect(() => validateBundle({ schema_version: "1.0" })).toThrow("missing meta");
    expect(() => validateBundle({ ...fixture, samples: {} })).toThrow(
      "sample collections are invalid",
    );
    await expect(
      loadBundle(vi.fn().mockResolvedValue(new Response("{", { status: 200 }))),
    ).rejects.toThrow("not valid JSON");
  });

  it("exposes loading and ready states through one cached provider request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(fixture), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(
      <BundleProvider>
        <StatusProbe />
      </BundleProvider>,
    );
    expect(screen.getByText("loading")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("15")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("requires the provider", () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    expect(() => render(<StatusProbe />)).toThrow("within BundleProvider");
    error.mockRestore();
  });
});

"use client";

import {
  createContext,
  createElement,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { DashboardBundle } from "./bundle.types";

export const BUNDLE_URL = "/data/bundle.json";
export const SUPPORTED_SCHEMA_VERSION = "1.0";

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export type BundleState =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: DashboardBundle; error: null }
  | { status: "error"; data: null; error: Error };

const loadingState: BundleState = { status: "loading", data: null, error: null };
const BundleContext = createContext<BundleState | null>(null);
let cachedBundle: Promise<DashboardBundle> | null = null;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validateBundle(value: unknown): DashboardBundle {
  if (!isRecord(value)) throw new Error("The data bundle is not a JSON object.");
  if (value.schema_version !== SUPPORTED_SCHEMA_VERSION) {
    const received = typeof value.schema_version === "string" ? value.schema_version : "missing";
    throw new Error(
      `Unsupported data bundle version ${received}; expected ${SUPPORTED_SCHEMA_VERSION}.`,
    );
  }
  for (const key of [
    "meta",
    "samples",
    "frequencies_long",
    "response_analysis",
    "baseline_subset",
    "form_answer",
    "run",
  ] as const) {
    if (!(key in value)) throw new Error(`The data bundle is missing ${key}.`);
  }
  if (!Array.isArray(value.samples) || !Array.isArray(value.frequencies_long)) {
    throw new Error("The data bundle sample collections are invalid.");
  }
  return value as unknown as DashboardBundle;
}

export async function loadBundle(fetcher: Fetcher = fetch): Promise<DashboardBundle> {
  const response = await fetcher(BUNDLE_URL, { cache: "no-store" });
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("No data bundle found. Run `make pipeline` to generate it.");
    }
    throw new Error(`Could not load the data bundle (HTTP ${response.status}).`);
  }
  try {
    return validateBundle(await response.json());
  } catch (error) {
    if (error instanceof SyntaxError) throw new Error("The data bundle is not valid JSON.");
    throw error;
  }
}

export function resetBundleCache(): void {
  cachedBundle = null;
}

function getBundle(): Promise<DashboardBundle> {
  cachedBundle ??= loadBundle();
  return cachedBundle;
}

export function BundleProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<BundleState>(loadingState);

  useEffect(() => {
    let active = true;
    getBundle().then(
      (data) => active && setState({ status: "ready", data, error: null }),
      (reason: unknown) => {
        const error =
          reason instanceof Error ? reason : new Error("Could not load the data bundle.");
        if (active) setState({ status: "error", data: null, error });
      },
    );
    return () => {
      active = false;
    };
  }, []);

  return createElement(BundleContext.Provider, { value: state }, children);
}

export function useBundle(): BundleState {
  const state = useContext(BundleContext);
  if (state === null) throw new Error("useBundle must be used within BundleProvider.");
  return state;
}

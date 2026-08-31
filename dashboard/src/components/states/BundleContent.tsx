"use client";

import type { ReactNode } from "react";

import { useBundle } from "@/lib/bundle";
import type { DashboardBundle } from "@/lib/bundle.types";

import { EmptyState, ErrorState, LoadingState } from "./DataStates";

export function BundleContent({ children }: { children: (bundle: DashboardBundle) => ReactNode }) {
  const state = useBundle();
  if (state.status === "loading") return <LoadingState />;
  if (state.status === "error") return <ErrorState message={state.error.message} />;
  if (state.data.samples.length === 0) {
    return <EmptyState message="No samples are available in this data bundle." />;
  }
  return children(state.data);
}

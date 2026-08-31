import type { DashboardBundle } from "./bundle.types";

export type BundleSample = DashboardBundle["samples"][number];
export type FilterField =
  | "project"
  | "condition"
  | "treatment"
  | "sample_type"
  | "time"
  | "response"
  | "sex";

export interface SampleFilters {
  project: string[];
  condition: string[];
  treatment: string[];
  sample_type: string[];
  time: string[];
  response: string[];
  sex: string[];
  search: string;
}

export const EMPTY_FILTERS: SampleFilters = {
  project: [],
  condition: [],
  treatment: [],
  sample_type: [],
  time: [],
  response: [],
  sex: [],
  search: "",
};

const FILTER_FIELDS: readonly FilterField[] = [
  "project",
  "condition",
  "treatment",
  "sample_type",
  "time",
  "response",
  "sex",
];

function sampleValue(sample: BundleSample, field: FilterField): string {
  const value = sample[field];
  return value === null ? "" : String(value);
}

export function filterSamples(samples: BundleSample[], filters: SampleFilters): BundleSample[] {
  const search = filters.search.trim().toLocaleLowerCase();
  return samples.filter((sample) => {
    const fieldsMatch = FILTER_FIELDS.every((field) => {
      const accepted = filters[field];
      return accepted.length === 0 || accepted.includes(sampleValue(sample, field));
    });
    const textMatches =
      search.length === 0 ||
      sample.sample.toLocaleLowerCase().includes(search) ||
      sample.subject.toLocaleLowerCase().includes(search);
    return fieldsMatch && textMatches;
  });
}

export function filterOptions(samples: BundleSample[], field: FilterField): string[] {
  return [...new Set(samples.map((sample) => sampleValue(sample, field)).filter(Boolean))].sort(
    (left, right) => left.localeCompare(right, undefined, { numeric: true }),
  );
}

export function parseFilters(params: URLSearchParams): SampleFilters {
  const parsed = { ...EMPTY_FILTERS, search: params.get("search") ?? "" };
  for (const field of FILTER_FIELDS) {
    parsed[field] = params.getAll(field).filter(Boolean);
  }
  return parsed;
}

export function serialiseFilters(filters: SampleFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const field of FILTER_FIELDS) {
    for (const value of filters[field]) params.append(field, value);
  }
  if (filters.search.trim()) params.set("search", filters.search.trim());
  return params;
}

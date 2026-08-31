"use client";

import { useId } from "react";

import {
  EMPTY_FILTERS,
  filterOptions,
  type BundleSample,
  type FilterField,
  type SampleFilters,
} from "@/lib/filters";

const FIELD_LABELS: Record<FilterField, string> = {
  project: "Project",
  condition: "Condition",
  treatment: "Treatment",
  sample_type: "Sample type",
  time: "Day",
  response: "Response",
  sex: "Sex",
};

const VALUE_LABELS: Partial<Record<FilterField, Record<string, string>>> = {
  response: { yes: "Responders", no: "Non-responders" },
  sex: { M: "Male", F: "Female" },
};

function valueLabel(field: FilterField, value: string): string {
  if (field === "time") return `day ${value}`;
  return VALUE_LABELS[field]?.[value] ?? value;
}

function FilterPopover({
  field,
  options,
  selected,
  onToggle,
}: {
  field: FilterField;
  options: string[];
  selected: string[];
  onToggle: (field: FilterField, value: string) => void;
}) {
  const label = FIELD_LABELS[field];
  return (
    <details className="filter-popover">
      <summary>
        {label}
        {selected.length > 0 ? <span className="filter-count">{selected.length}</span> : null}
      </summary>
      <fieldset>
        <legend className="visually-hidden">{label} filters</legend>
        {options.map((option) => (
          <label key={option}>
            <input
              checked={selected.includes(option)}
              onChange={() => onToggle(field, option)}
              type="checkbox"
              value={option}
            />
            {valueLabel(field, option)}
          </label>
        ))}
      </fieldset>
    </details>
  );
}

export function FilterBar({
  samples,
  filters,
  onChange,
}: {
  samples: BundleSample[];
  filters: SampleFilters;
  onChange: (filters: SampleFilters) => void;
}) {
  const searchId = useId();
  const fields = Object.keys(FIELD_LABELS) as FilterField[];
  const active =
    fields.some((field) => filters[field].length > 0) || filters.search.trim().length > 0;

  const toggle = (field: FilterField, value: string) => {
    const current = filters[field];
    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];
    onChange({ ...filters, [field]: next });
  };

  return (
    <form className="filter-bar" onSubmit={(event) => event.preventDefault()} role="search">
      {fields.map((field) => (
        <FilterPopover
          field={field}
          key={field}
          onToggle={toggle}
          options={filterOptions(samples, field)}
          selected={filters[field]}
        />
      ))}
      <label className="filter-search" htmlFor={searchId}>
        <span className="visually-hidden">Sample or subject id</span>
        <input
          id={searchId}
          onChange={(event) => onChange({ ...filters, search: event.target.value })}
          placeholder="Sample or subject id"
          type="search"
          value={filters.search}
        />
      </label>
      <button disabled={!active} onClick={() => onChange(EMPTY_FILTERS)} type="button">
        Clear filters
      </button>
    </form>
  );
}

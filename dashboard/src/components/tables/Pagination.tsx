"use client";

import { formatCount } from "@/lib/stats-format";

export function pageWindow(page: number, pageCount: number): (number | "gap")[] {
  if (pageCount <= 7) return Array.from({ length: pageCount }, (_, index) => index + 1);
  const middle = [page - 1, page, page + 1].filter(
    (candidate) => candidate > 1 && candidate < pageCount,
  );
  const items: (number | "gap")[] = [1];
  if (middle.length === 0 || middle[0] > 2) items.push("gap");
  items.push(...middle);
  if (middle.length === 0 || middle[middle.length - 1] < pageCount - 1) items.push("gap");
  items.push(pageCount);
  return items;
}

export function Pagination({
  page,
  pageSize,
  totalRows,
  onChange,
  label,
}: {
  page: number;
  pageSize: number;
  totalRows: number;
  onChange: (page: number) => void;
  label: string;
}) {
  const pageCount = Math.max(1, Math.ceil(totalRows / pageSize));
  const clamped = Math.min(Math.max(1, page), pageCount);
  const first = (clamped - 1) * pageSize + 1;
  const last = Math.min(clamped * pageSize, totalRows);
  if (totalRows === 0) return null;
  return (
    <nav aria-label={`${label} pages`} className="pagination">
      <p aria-live="polite">
        Rows {formatCount(first)}–{formatCount(last)} of {formatCount(totalRows)}
      </p>
      {pageCount > 1 ? (
        <div className="pagination-controls">
          <button
            aria-label="Previous page"
            disabled={clamped === 1}
            onClick={() => onChange(clamped - 1)}
            type="button"
          >
            Previous
          </button>
          {pageWindow(clamped, pageCount).map((item, index) =>
            item === "gap" ? (
              <span aria-hidden="true" className="page-gap" key={`gap-${index}`}>
                …
              </span>
            ) : (
              <button
                aria-current={item === clamped ? "page" : undefined}
                aria-label={`Page ${item}`}
                className={item === clamped ? "page-current" : undefined}
                key={item}
                onClick={() => onChange(item)}
                type="button"
              >
                {formatCount(item)}
              </button>
            ),
          )}
          <button
            aria-label="Next page"
            disabled={clamped === pageCount}
            onClick={() => onChange(clamped + 1)}
            type="button"
          >
            Next
          </button>
        </div>
      ) : null}
    </nav>
  );
}

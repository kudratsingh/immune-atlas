const countFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const percentageFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
});

export function formatCount(value: number): string {
  return countFormatter.format(value);
}

export function formatPercentage(value: number | null, digits = 2): string {
  if (value === null || !Number.isFinite(value)) return "Not available";
  return `${percentageFormatter.format(Number(value.toFixed(digits)))}%`;
}

export function formatPValue(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Not available";
  if (value < 0.001) return "<0.001";
  return value.toFixed(3).replace(/^0/, "");
}

export function formatEffectSize(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Not available";
  return value.toFixed(2);
}

export function pluralise(value: number, singular: string, plural = `${singular}s`): string {
  return `${formatCount(value)} ${value === 1 ? singular : plural}`;
}

import { formatCount } from "@/lib/stats-format";

export interface CohortStep {
  label: string;
  count: number;
  unit?: string;
}

function connectorPath(fromCount: number, toCount: number, max: number): string {
  const height = (count: number) => 6 + 30 * (count / max);
  const from = height(fromCount) / 2;
  const to = height(toCount) / 2;
  return `M 0 ${24 - from} L 44 ${24 - to} L 44 ${24 + to} L 0 ${24 + from} Z`;
}

export function CohortStrip({
  title = "Cohort",
  steps,
  funnel = false,
}: {
  title?: string;
  steps: CohortStep[];
  funnel?: boolean;
}) {
  const max = Math.max(...steps.map((step) => step.count), 1);
  return (
    <section
      className={funnel ? "cohort-strip cohort-strip-funnel" : "cohort-strip"}
      aria-labelledby="cohort-strip-title"
    >
      <h2 id="cohort-strip-title">{title}</h2>
      <ol>
        {steps.map((step, index) => (
          <li key={`${step.label}-${index}`}>
            <span>{step.label}</span>
            <strong>{formatCount(step.count)}</strong>
            {step.unit ? <small>{step.unit}</small> : null}
            {funnel && index < steps.length - 1 ? (
              <svg
                aria-hidden="true"
                className="strip-connector"
                preserveAspectRatio="none"
                viewBox="0 0 44 48"
              >
                <path
                  d={connectorPath(step.count, steps[index + 1].count, max)}
                  fill="currentColor"
                />
              </svg>
            ) : null}
          </li>
        ))}
      </ol>
    </section>
  );
}

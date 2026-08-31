import { formatCount } from "@/lib/stats-format";

export interface CohortStep {
  label: string;
  count: number;
  unit?: string;
}

export function CohortStrip({ title = "Cohort", steps }: { title?: string; steps: CohortStep[] }) {
  return (
    <section className="cohort-strip" aria-labelledby="cohort-strip-title">
      <h2 id="cohort-strip-title">{title}</h2>
      <ol>
        {steps.map((step, index) => (
          <li key={`${step.label}-${index}`}>
            <span>{step.label}</span>
            <strong>{formatCount(step.count)}</strong>
            {step.unit ? <small>{step.unit}</small> : null}
          </li>
        ))}
      </ol>
    </section>
  );
}

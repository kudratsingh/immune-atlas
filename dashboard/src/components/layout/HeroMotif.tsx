import { PALETTE } from "@/lib/palette";

function cloud(seed: number, cx: number, cy: number, count: number): [number, number, number][] {
  let state = seed;
  const next = () => {
    state = (state * 48271) % 2147483647;
    return state / 2147483647;
  };
  return Array.from({ length: count }, () => {
    const angle = next() * Math.PI * 2;
    const radius = (next() + next()) * 46;
    return [cx + Math.cos(angle) * radius * 1.35, cy + Math.sin(angle) * radius, 2 + next() * 2.4];
  });
}

/* Two cell populations as a cytometry-style dot cloud — the subject's own imagery. */
export function HeroMotif() {
  return (
    <svg fill="none" height="170" viewBox="0 0 340 170" width="340">
      {cloud(7, 118, 92, 60).map(([x, y, r], index) => (
        <circle cx={x} cy={y} fill={PALETTE.responder} key={`a-${index}`} opacity={0.5} r={r} />
      ))}
      {cloud(23, 236, 74, 48).map(([x, y, r], index) => (
        <circle cx={x} cy={y} fill={PALETTE.nonResponder} key={`b-${index}`} opacity={0.42} r={r} />
      ))}
    </svg>
  );
}

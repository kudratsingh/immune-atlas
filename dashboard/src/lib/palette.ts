export const PALETTE = {
  paper: "#F4F7FA",
  panel: "#FFFFFF",
  ink: "#14213D",
  inkMuted: "#5B6B84",
  rule: "#D6DEE8",
  responder: "#0E7490",
  nonResponder: "#B45309",
  focus: "#1D4ED8",
  populations: ["#1E3A8A", "#2F55B3", "#4F7BD9", "#86A8EA", "#BFD3F3"],
} as const;

export type ResponseGroup = "yes" | "no";

export function responseColour(response: ResponseGroup): string {
  return response === "yes" ? PALETTE.responder : PALETTE.nonResponder;
}

export function populationColour(sortOrder: number): string {
  return PALETTE.populations[Math.max(0, Math.min(sortOrder, PALETTE.populations.length - 1))];
}

import { PALETTE } from "@/lib/palette";

interface TableBox {
  name: string;
  columns: string[];
  x: number;
  y: number;
}

const TABLES: TableBox[] = [
  { name: "projects", columns: ["project_id"], x: 10, y: 10 },
  {
    name: "subjects",
    columns: ["subject_id, condition, age, sex,", "treatment, response"],
    x: 10,
    y: 104,
  },
  {
    name: "samples",
    columns: ["sample_id, sample_type,", "time_from_treatment_start"],
    x: 10,
    y: 198,
  },
  { name: "cell_populations", columns: ["population_id, name, display_name"], x: 320, y: 104 },
  { name: "cell_counts", columns: ["sample_id, population_id, count"], x: 320, y: 198 },
];

const LINKS: [string, string][] = [
  ["projects", "subjects"],
  ["subjects", "samples"],
  ["samples", "cell_counts"],
  ["cell_populations", "cell_counts"],
];

const WIDTH = 260;
const HEIGHT = 74;

function centre(name: string): { x: number; y: number } {
  const box = TABLES.find((table) => table.name === name);
  if (!box) return { x: 0, y: 0 };
  return { x: box.x + WIDTH / 2, y: box.y + HEIGHT / 2 };
}

export function SchemaDiagram() {
  return (
    <div className="schema-diagram">
      <svg
        viewBox="0 0 590 284"
        role="img"
        aria-label="Database schema: projects contain subjects, subjects contain samples, and cell counts join samples with cell populations"
      >
        {LINKS.map(([from, to]) => {
          const a = centre(from);
          const b = centre(to);
          return (
            <line
              key={`${from}-${to}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={PALETTE.inkMuted}
              strokeWidth={1.5}
            />
          );
        })}
        {TABLES.map((table) => (
          <g key={table.name}>
            <rect
              x={table.x}
              y={table.y}
              width={WIDTH}
              height={HEIGHT}
              rx={8}
              fill={PALETTE.panel}
              stroke={PALETTE.rule}
            />
            <text
              x={table.x + 14}
              y={table.y + 26}
              fill={PALETTE.ink}
              fontSize={14}
              fontWeight={600}
            >
              {table.name}
            </text>
            {table.columns.map((line, index) => (
              <text
                key={line}
                x={table.x + 14}
                y={table.y + 46 + index * 15}
                fill={PALETTE.inkMuted}
                fontSize={10.5}
              >
                {line}
              </text>
            ))}
          </g>
        ))}
      </svg>
    </div>
  );
}

import type { ReactNode } from "react";

export interface DataColumn<Row> {
  id: string;
  header: string;
  numeric?: boolean;
  render: (row: Row) => ReactNode;
}

export function DataTable<Row>({
  caption,
  columns,
  rows,
  getRowKey,
}: {
  caption: string;
  columns: DataColumn<Row>[];
  rows: Row[];
  getRowKey: (row: Row, index: number) => string;
}) {
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label={`${caption}, scrollable`}>
      <table className="data-table">
        <caption>{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th className={column.numeric ? "numeric" : undefined} key={column.id} scope="col">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={getRowKey(row, index)}>
              {columns.map((column, columnIndex) => (
                <td
                  className={column.numeric ? "numeric" : columnIndex === 0 ? "pinned" : undefined}
                  key={column.id}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import type { ReactNode } from 'react';

interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  width?: string;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  empty?: string;
}

export function Table<T>({ columns, rows, rowKey, empty }: Props<T>) {
  if (rows.length === 0) {
    return <div className="empty">{empty ?? 'No records.'}</div>;
  }
  return (
    <table>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key} style={c.width ? { width: c.width } : undefined}>{c.header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={rowKey(row)}>
            {columns.map((c) => (
              <td key={c.key}>
                {c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? '')}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

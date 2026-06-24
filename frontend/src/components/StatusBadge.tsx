import type { SetStatus } from '../api/types';

export function StatusBadge({ status }: { status: SetStatus }) {
  return <span className={`badge ${status}`}>{status}</span>;
}

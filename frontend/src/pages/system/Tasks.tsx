import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import type { SystemTask } from '../../api/types';
import { Table } from '../../components/Table';

export function Tasks() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['system', 'tasks'],
    queryFn: () => api<SystemTask[] | { records: SystemTask[] }>('/system/tasks'),
  });
  if (isLoading) return <div className="empty">Loading…</div>;
  if (error) return <div className="empty">Could not load tasks.</div>;
  const rows: SystemTask[] = Array.isArray(data) ? data : (data?.records ?? []);
  return (
    <Table<SystemTask>
      rowKey={(r) => r.name}
      empty="No tasks scheduled."
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'interval', header: 'Interval' },
        { key: 'lastRun', header: 'Last Run', render: (r) => r.lastRun ?? '—' },
        { key: 'nextRun', header: 'Next Run', render: (r) => r.nextRun ?? '—' },
        { key: 'lastDuration', header: 'Last Duration', render: (r) => r.lastDuration ?? '—' },
      ]}
      rows={rows}
    />
  );
}

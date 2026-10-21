import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import type { SystemStatus } from '../../api/types';
import { Card } from '../../components/Card';

function YesNo({ value }: { value: boolean | null | undefined }) {
  if (value === undefined || value === null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
  return <span style={{ color: value ? 'var(--success)' : 'var(--danger)' }}>{value ? 'Yes' : 'No'}</span>;
}

export function Status() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['system', 'status'],
    queryFn: () => api<SystemStatus>('/system/status'),
    refetchInterval: 10_000,
  });
  if (isLoading) return <div className="empty">Loading…</div>;
  if (error || !data) return <div className="empty">Could not load status.</div>;

  return (
    <Card title="System Status">
      <div className="meta-grid">
        <div className="item"><div className="label">Version</div><div className="value">{data.version}</div></div>
        <div className="item"><div className="label">Database</div><div className="value">{data.dbType === 'mariadb' ? 'MariaDB' : 'SQLite'}</div></div>
        <div className="item"><div className="label">Database Connected</div><div className="value"><YesNo value={data.dbOk} /></div></div>
        <div className="item"><div className="label">Brickset Reachable</div><div className="value"><YesNo value={data.sources?.brickset} /></div></div>
      </div>
    </Card>
  );
}

import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import type { SystemStatus } from '../../api/types';
import { Card } from '../../components/Card';

function YesNo({ value }: { value: boolean | undefined }) {
  if (value === undefined) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
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
        <div className="item"><div className="label">Database</div><div className="value"><YesNo value={data.database?.connected} /></div></div>
        <div className="item"><div className="label">BrickLink Reachable</div><div className="value"><YesNo value={data.dataSources?.bricklink?.reachable} /></div></div>
        <div className="item"><div className="label">Brickset Reachable</div><div className="value"><YesNo value={data.dataSources?.brickset?.reachable} /></div></div>
        <div className="item">
          <div className="label">BrickLink Budget Remaining</div>
          <div className="value">
            {data.dataSources?.bricklink?.budgetRemaining ?? '—'} / {data.dataSources?.bricklink?.budgetCap ?? '—'}
          </div>
        </div>
      </div>
    </Card>
  );
}

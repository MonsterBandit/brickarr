import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import type { Paged, SetSummary } from '../../api/types';
import { PageHeader } from '../../components/PageHeader';
import { StatusBadge } from '../../components/StatusBadge';

export function SetsGrid() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['sets'],
    queryFn: () => api<Paged<SetSummary>>('/sets'),
  });

  return (
    <div className="page">
      <PageHeader
        title="Sets"
        subtitle="Your collection"
        actions={<Link to="/sets/add"><button className="primary">Add New</button></Link>}
      />
      {isLoading && <div className="empty">Loading…</div>}
      {error && <div className="empty">Could not load sets.</div>}
      {data && data.records.length === 0 && (
        <div className="card empty">
          <div style={{ marginBottom: 'var(--space-3)' }}>No sets yet.</div>
          <Link to="/sets/add"><button className="primary">Add your first set</button></Link>
        </div>
      )}
      {data && data.records.length > 0 && (
        <div className="grid">
          {data.records.map((s) => (
            <Link key={s.id} to={`/sets/${s.id}`} style={{ color: 'inherit' }}>
              <div className="set-card">
                <div className="thumb">
                  {s.thumbnailUrl || s.imageUrl ? (
                    <img src={s.thumbnailUrl ?? s.imageUrl} alt={s.name} />
                  ) : (
                    <span>No image</span>
                  )}
                </div>
                <div className="meta">
                  <div className="name">{s.name}</div>
                  <div className="num">{s.setNumber}</div>
                  <div className="row">
                    <StatusBadge status={s.status} />
                    {s.stats && (
                      <span>{s.stats.owned}/{s.stats.owned + s.stats.missing}</span>
                    )}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

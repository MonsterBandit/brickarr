import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import type { SetDetail as TSetDetail, SetPartRow, InstructionRow, Paged } from '../../api/types';
import { PageHeader } from '../../components/PageHeader';
import { StatusBadge } from '../../components/StatusBadge';
import { Card } from '../../components/Card';
import { Table } from '../../components/Table';
import { useToast } from '../../components/Toast';

type PartsFilter = 'all' | 'owned' | 'missing';

export function SetDetail() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const [filter, setFilter] = useState<PartsFilter>('all');

  const setQ = useQuery({
    queryKey: ['set', id],
    queryFn: () => api<TSetDetail>(`/sets/${id}`),
    enabled: !!id,
  });

  const partsQ = useQuery({
    queryKey: ['set-parts', id, filter],
    queryFn: () => api<Paged<SetPartRow>>(`/sets/${id}/parts`, { query: { filter } }),
    enabled: !!id,
  });

  const instQ = useQuery({
    queryKey: ['set-instructions', id],
    queryFn: () => api<InstructionRow[]>(`/sets/${id}/instructions`),
    enabled: !!id,
  });

  async function downloadInstructions() {
    try {
      await api(`/sets/${id}/instructions/download`, { method: 'POST', body: {} });
      toast('success', 'Instruction download queued');
    } catch {
      toast('error', 'Could not queue download');
    }
  }

  if (setQ.isLoading) return <div className="page"><div className="empty">Loading…</div></div>;
  if (setQ.error || !setQ.data) return <div className="page"><div className="empty">Could not load set.</div></div>;
  const s = setQ.data;

  const partsRows: SetPartRow[] = (partsQ.data?.records ?? []) as SetPartRow[];
  const instructions = instQ.data ?? [];

  return (
    <div className="page">
      <PageHeader
        title={s.name}
        subtitle={s.setNumber}
        actions={<StatusBadge status={s.status} />}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 'var(--space-5)', marginBottom: 'var(--space-5)' }}>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {s.imageUrl ? (
            <img src={s.imageUrl} alt={s.name} style={{ width: '100%', height: 'auto', display: 'block' }} />
          ) : (
            <div className="empty" style={{ aspectRatio: '4/3' }}>No image</div>
          )}
        </div>
        <Card title="Overview">
          <div className="stat-row">
            <div className="stat"><div className="label">Owned</div><div className="value">{s.stats.owned}</div></div>
            <div className="stat"><div className="label">Missing</div><div className="value">{s.stats.missing}</div></div>
            <div className="stat"><div className="label">Price / Piece</div><div className="value">{s.stats.pricePerPiece?.toFixed(2) ?? '—'}</div></div>
          </div>
          <div className="meta-grid">
            <div className="item"><div className="label">Theme</div><div className="value">{s.theme ?? '—'}{s.subtheme ? ` / ${s.subtheme}` : ''}</div></div>
            <div className="item"><div className="label">Year</div><div className="value">{s.year ?? '—'}</div></div>
            <div className="item"><div className="label">RRP</div><div className="value">{s.rrp ?? '—'}</div></div>
            <div className="item"><div className="label">Acquired Price</div><div className="value">{s.acquiredPrice ?? '—'}</div></div>
            <div className="item"><div className="label">Acquired Date</div><div className="value">{s.acquiredDate ?? '—'}</div></div>
            <div className="item"><div className="label">Storage Location</div><div className="value">{s.storageLocation ?? '—'}</div></div>
          </div>
        </Card>
      </div>

      <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Parts Manifest</h3>
        </div>
        <div className="pills">
          {(['all', 'owned', 'missing'] as const).map((f) => (
            <button key={f} className={`pill${filter === f ? ' active' : ''}`} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>
        {partsQ.isLoading ? (
          <div className="empty">Loading parts…</div>
        ) : (
          <Table<SetPartRow>
            rowKey={(r) => r.setPartId}
            empty="No parts."
            columns={[
              { key: 'partNo', header: 'Part #', render: (r) => r.partNo },
              { key: 'name', header: 'Name', render: (r) => r.name },
              {
                key: 'color', header: 'Colour',
                render: (r) => <span className="badge" style={{ textTransform: 'none' }}>{r.colorName}</span>,
              },
              { key: 'quantity', header: 'Qty', render: (r) => r.quantity },
              { key: 'owned', header: 'Owned', render: (r) => r.owned },
              { key: 'missing', header: 'Missing', render: (r) => r.missing },
            ]}
            rows={partsRows}
          />
        )}
      </div>

      <Card
        title="Instructions"
        actions={<button onClick={downloadInstructions}>Download All</button>}
      >
        {instructions.length === 0 ? (
          <div className="empty">No instructions listed.</div>
        ) : (
          <Table<InstructionRow>
            rowKey={(r) => r.id}
            columns={[
              { key: 'description', header: 'Description' },
              { key: 'downloaded', header: 'Downloaded', render: (r) => (r.downloaded ? 'Yes' : 'No') },
              { key: 'sizeBytes', header: 'Size', render: (r) => (r.sizeBytes ? `${(r.sizeBytes / 1024 / 1024).toFixed(2)} MB` : '—') },
            ]}
            rows={instructions}
          />
        )}
      </Card>
    </div>
  );
}

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { QueueItem, HistoryItem, Paged } from '../api/types';
import { PageHeader } from '../components/PageHeader';
import { Table } from '../components/Table';
import { ProgressBar } from '../components/ProgressBar';

type Tab = 'queue' | 'history';

export function Activity() {
  const [tab, setTab] = useState<Tab>('queue');
  return (
    <div className="page">
      <PageHeader title="Activity" subtitle="Live jobs and history" />
      <div className="tabs">
        <div className={`tab${tab === 'queue' ? ' active' : ''}`} onClick={() => setTab('queue')}>Queue</div>
        <div className={`tab${tab === 'history' ? ' active' : ''}`} onClick={() => setTab('history')}>History</div>
      </div>
      {tab === 'queue' ? <Queue /> : <History />}
    </div>
  );
}

function Queue() {
  const { data, isLoading } = useQuery({
    queryKey: ['queue'],
    queryFn: () => api<Paged<QueueItem> | QueueItem[]>('/queue'),
    refetchInterval: 2000,
  });
  if (isLoading) return <div className="empty">Loading…</div>;
  const rows: QueueItem[] = Array.isArray(data) ? data : (data?.records ?? []);
  return (
    <Table<QueueItem>
      rowKey={(r) => r.id}
      empty="Queue is empty."
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'status', header: 'Status' },
        {
          key: 'progress', header: 'Progress',
          render: (r) => (r.total ? <ProgressBar value={r.progress} max={r.total} /> : '—'),
        },
        { key: 'startedAt', header: 'Started', render: (r) => r.startedAt ?? '—' },
      ]}
      rows={rows}
    />
  );
}

function History() {
  const { data, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => api<Paged<HistoryItem> | HistoryItem[]>('/history'),
  });
  if (isLoading) return <div className="empty">Loading…</div>;
  const rows: HistoryItem[] = Array.isArray(data) ? data : (data?.records ?? []);
  return (
    <Table<HistoryItem>
      rowKey={(r) => r.id}
      empty="No history yet."
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'kind', header: 'Kind' },
        { key: 'status', header: 'Status' },
        { key: 'finishedAt', header: 'Finished', render: (r) => r.finishedAt ?? '—' },
      ]}
      rows={rows}
    />
  );
}

import { useEffect, useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, ApiError } from '../../api/client';
import { Card } from '../../components/Card';
import { useToast } from '../../components/Toast';
import type { SystemStatus } from '../../api/types';

interface BrickLinkCreds {
  consumerKey: string;
  consumerSecret: string;
  tokenValue: string;
  tokenSecret: string;
}
interface BricksetCreds {
  apiKey: string;
  userHash: string;
}

interface SettingValue<T> { value: T; }

const BL_DEFAULT: BrickLinkCreds = { consumerKey: '', consumerSecret: '', tokenValue: '', tokenSecret: '' };
const BS_DEFAULT: BricksetCreds = { apiKey: '', userHash: '' };

export function DataSources() {
  const toast = useToast();

  const blQ = useQuery({
    queryKey: ['settings', 'bricklink'],
    queryFn: () => api<SettingValue<BrickLinkCreds>>('/settings/datasources/bricklink'),
  });
  const bsQ = useQuery({
    queryKey: ['settings', 'brickset'],
    queryFn: () => api<SettingValue<BricksetCreds>>('/settings/datasources/brickset'),
  });
  const statusQ = useQuery({
    queryKey: ['system', 'status'],
    queryFn: () => api<SystemStatus>('/system/status'),
  });

  const [bl, setBl] = useState<BrickLinkCreds>(BL_DEFAULT);
  const [bs, setBs] = useState<BricksetCreds>(BS_DEFAULT);

  useEffect(() => { if (blQ.data?.value) setBl({ ...BL_DEFAULT, ...blQ.data.value }); }, [blQ.data]);
  useEffect(() => { if (bsQ.data?.value) setBs({ ...BS_DEFAULT, ...bsQ.data.value }); }, [bsQ.data]);

  const saveBl = useMutation({
    mutationFn: (body: BrickLinkCreds) =>
      api('/settings/datasources/bricklink', { method: 'PUT', body: { value: body } }),
    onSuccess: () => toast('success', 'BrickLink saved'),
    onError: () => toast('error', 'Save failed'),
  });
  const saveBs = useMutation({
    mutationFn: (body: BricksetCreds) =>
      api('/settings/datasources/brickset', { method: 'PUT', body: { value: body } }),
    onSuccess: () => toast('success', 'Brickset saved'),
    onError: () => toast('error', 'Save failed'),
  });

  async function test(source: 'bricklink' | 'brickset') {
    try {
      await api(`/settings/datasources/${source}/test`, { method: 'POST', body: {} });
      toast('success', `${source} reachable`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        toast('Test endpoint not yet available');
      } else {
        toast('error', `${source} test failed`);
      }
    }
  }

  const blBudget = statusQ.data?.dataSources.bricklink;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', maxWidth: 720 }}>
      <Card
        title="BrickLink"
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button onClick={() => test('bricklink')}>Test</button>
            <button className="primary" onClick={() => saveBl.mutate(bl)} disabled={saveBl.isPending}>Save</button>
          </div>
        }
      >
        <div className="form-grid">
          <div className="form-row">
            <label>Consumer Key</label>
            <input value={bl.consumerKey} onChange={(e) => setBl({ ...bl, consumerKey: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Consumer Secret</label>
            <input type="password" value={bl.consumerSecret} onChange={(e) => setBl({ ...bl, consumerSecret: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Token Value</label>
            <input value={bl.tokenValue} onChange={(e) => setBl({ ...bl, tokenValue: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Token Secret</label>
            <input type="password" value={bl.tokenSecret} onChange={(e) => setBl({ ...bl, tokenSecret: e.target.value })} />
          </div>
        </div>
        <div style={{ marginTop: 'var(--space-3)', fontSize: 13, color: 'var(--text-dim)' }}>
          Daily BrickLink budget: {blBudget?.budgetRemaining ?? '—'} / {blBudget?.budgetCap ?? '—'} remaining
        </div>
      </Card>

      <Card
        title="Brickset"
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button onClick={() => test('brickset')}>Test</button>
            <button className="primary" onClick={() => saveBs.mutate(bs)} disabled={saveBs.isPending}>Save</button>
          </div>
        }
      >
        <div className="form-grid">
          <div className="form-row">
            <label>API Key</label>
            <input type="password" value={bs.apiKey} onChange={(e) => setBs({ ...bs, apiKey: e.target.value })} />
          </div>
          <div className="form-row">
            <label>User Hash (optional)</label>
            <input value={bs.userHash} onChange={(e) => setBs({ ...bs, userHash: e.target.value })} />
          </div>
        </div>
      </Card>
    </div>
  );
}

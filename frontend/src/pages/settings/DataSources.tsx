import { useEffect, useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, ApiError } from '../../api/client';
import { Card } from '../../components/Card';
import { useToast } from '../../components/Toast';

// The BrickLink API client is gone (BRK-31). The Rebrickable catalogue source
// and its settings card arrive in BR.DK.09.
interface BricksetCreds {
  apiKey: string;
  userHash: string;
}

interface SettingValue<T> { value: T; }

const BS_DEFAULT: BricksetCreds = { apiKey: '', userHash: '' };

export function DataSources() {
  const toast = useToast();

  const bsQ = useQuery({
    queryKey: ['settings', 'brickset'],
    queryFn: () => api<SettingValue<BricksetCreds>>('/settings/datasources/brickset'),
  });
  const [bs, setBs] = useState<BricksetCreds>(BS_DEFAULT);

  useEffect(() => { if (bsQ.data?.value) setBs({ ...BS_DEFAULT, ...bsQ.data.value }); }, [bsQ.data]);

  const saveBs = useMutation({
    mutationFn: (body: BricksetCreds) =>
      api('/settings/datasources/brickset', { method: 'PUT', body: { value: body } }),
    onSuccess: () => toast('success', 'Brickset saved'),
    onError: () => toast('error', 'Save failed'),
  });

  async function test(source: 'brickset') {
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', maxWidth: 720 }}>
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

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../api/client';
import type { ApiKey, AuthMode } from '../../api/types';
import { Card } from '../../components/Card';
import { useToast } from '../../components/Toast';

interface AuthModeSetting { value: AuthMode; }

function maskKey(k: string): string {
  if (!k) return '';
  if (k.length <= 4) return k;
  return '•'.repeat(Math.max(8, k.length - 4)) + k.slice(-4);
}

export function General() {
  const qc = useQueryClient();
  const toast = useToast();
  const [reveal, setReveal] = useState(false);

  const keysQ = useQuery({
    queryKey: ['apikeys'],
    queryFn: () => api<ApiKey[]>('/apikeys'),
  });

  const authQ = useQuery({
    queryKey: ['setting', 'auth_mode'],
    queryFn: () => api<AuthModeSetting>('/settings/auth_mode'),
  });

  const regen = useMutation({
    mutationFn: async () => {
      const list = keysQ.data ?? [];
      const def = list.find((k) => k.name === 'default') ?? list[0];
      if (def) await api(`/apikeys/${def.id}`, { method: 'DELETE' });
      return api<ApiKey>('/apikeys', { method: 'POST', body: { name: 'default' } });
    },
    onSuccess: () => {
      toast('success', 'API key regenerated');
      qc.invalidateQueries({ queryKey: ['apikeys'] });
    },
    onError: () => toast('error', 'Could not regenerate key'),
  });

  const setAuth = useMutation({
    mutationFn: (value: AuthMode) =>
      api('/settings/auth_mode', { method: 'PUT', body: { value } }),
    onSuccess: () => {
      toast('success', 'Auth mode saved');
      qc.invalidateQueries({ queryKey: ['setting', 'auth_mode'] });
    },
    onError: () => toast('error', 'Could not save auth mode'),
  });

  const defaultKey = (keysQ.data ?? []).find((k) => k.name === 'default') ?? (keysQ.data ?? [])[0];
  const keyValue = defaultKey?.key ?? defaultKey?.keyPrefix ?? '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', maxWidth: 720 }}>
      <Card title="API Key">
        {keysQ.isLoading ? (
          <div className="empty">Loading…</div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
              <code style={{ flex: 1, padding: 'var(--space-2)', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                {reveal ? keyValue : maskKey(keyValue)}
              </code>
              <button onClick={() => setReveal((x) => !x)}>{reveal ? 'Hide' : 'Show'}</button>
              <button className="danger" onClick={() => regen.mutate()} disabled={regen.isPending}>
                {regen.isPending ? 'Regenerating…' : 'Regenerate'}
              </button>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Send as <code>X-Api-Key</code> header on requests to <code>/api/v1/*</code>.
            </div>
          </>
        )}
      </Card>

      <Card title="UI Auth Mode">
        {authQ.isLoading ? (
          <div className="empty">Loading…</div>
        ) : (
          <select
            value={authQ.data?.value ?? 'forms'}
            onChange={(e) => setAuth.mutate(e.target.value as AuthMode)}
            style={{ maxWidth: 320 }}
          >
            <option value="forms">Forms</option>
            <option value="disabled-for-local">Disabled for Local Addresses</option>
            <option value="external">External</option>
          </select>
        )}
      </Card>
    </div>
  );
}

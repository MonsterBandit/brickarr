import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useAuth } from '../store/auth';
import type { AuthLoginResponse, ApiKey } from '../api/types';

export function Login() {
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);
  const setApiKey = useAuth((s) => s.setApiKey);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const resp = await api<AuthLoginResponse>('/login', {
        method: 'POST',
        body: { username, password },
      });
      setUser(resp.user ?? username);
      try {
        const keys = await api<ApiKey[]>('/apikeys');
        const first = keys[0];
        if (first?.key) setApiKey(first.key);
      } catch { /* ignore — session cookie still valid */ }
      navigate('/sets', { replace: true });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Login failed';
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Brickarr</h1>
        <div className="form-row">
          <label htmlFor="username">Username</label>
          <input id="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="form-row">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <div style={{ color: 'var(--danger)', marginBottom: 'var(--space-3)', fontSize: 13 }}>{error}</div>}
        <button type="submit" className="primary" disabled={busy} style={{ width: '100%' }}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}

import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiError } from '../../api/client';
import { PageHeader } from '../../components/PageHeader';
import { useToast } from '../../components/Toast';
import type { SetStatus, Condition } from '../../api/types';

interface FormState {
  setNumber: string;
  status: SetStatus;
  condition: Condition | '';
  copies: number;
  storageLocation: string;
  acquiredPrice: string;
  acquiredDate: string;
}

const initial: FormState = {
  setNumber: '',
  status: 'complete',
  condition: '',
  copies: 1,
  storageLocation: '',
  acquiredPrice: '',
  acquiredDate: '',
};

export function AddNew() {
  const [form, setForm] = useState<FormState>(initial);
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    const body: Record<string, unknown> = {
      setNumber: form.setNumber.trim(),
      status: form.status,
      copies: form.copies,
    };
    if (form.condition) body.condition = form.condition;
    if (form.storageLocation) body.storageLocation = form.storageLocation;
    if (form.acquiredPrice) body.acquiredPrice = Number(form.acquiredPrice);
    if (form.acquiredDate) body.acquiredDate = form.acquiredDate;

    try {
      await api('/sets', { method: 'POST', body });
      toast('success', 'Add queued');
      navigate('/activity');
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Add failed';
      toast('error', msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page" style={{ maxWidth: 640 }}>
      <PageHeader title="Add New Set" subtitle="Enqueues a manifest pull from BrickLink + Brickset enrichment." />
      <form onSubmit={onSubmit} className="card">
        <div className="form-row">
          <label>Set Number</label>
          <input value={form.setNumber} onChange={(e) => update('setNumber', e.target.value)} placeholder="43022-1" required />
        </div>
        <div className="form-grid">
          <div className="form-row">
            <label>Status</label>
            <select value={form.status} onChange={(e) => update('status', e.target.value as SetStatus)}>
              <option value="complete">complete</option>
              <option value="collecting">collecting</option>
              <option value="wanted">wanted</option>
              <option value="dismantled">dismantled</option>
            </select>
          </div>
          <div className="form-row">
            <label>Condition</label>
            <select value={form.condition} onChange={(e) => update('condition', e.target.value as Condition | '')}>
              <option value="">—</option>
              <option value="new">new</option>
              <option value="used">used</option>
            </select>
          </div>
          <div className="form-row">
            <label>Copies</label>
            <input type="number" min={1} value={form.copies} onChange={(e) => update('copies', Number(e.target.value))} />
          </div>
          <div className="form-row">
            <label>Storage Location</label>
            <input value={form.storageLocation} onChange={(e) => update('storageLocation', e.target.value)} placeholder="Bin A3" />
          </div>
          <div className="form-row">
            <label>Acquired Price</label>
            <input type="number" step="0.01" value={form.acquiredPrice} onChange={(e) => update('acquiredPrice', e.target.value)} />
          </div>
          <div className="form-row">
            <label>Acquired Date</label>
            <input type="date" value={form.acquiredDate} onChange={(e) => update('acquiredDate', e.target.value)} />
          </div>
        </div>
        <button type="submit" className="primary" disabled={busy}>{busy ? 'Submitting…' : 'Add Set'}</button>
      </form>
    </div>
  );
}

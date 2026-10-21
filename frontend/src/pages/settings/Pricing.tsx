import { useEffect, useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Card } from '../../components/Card';
import { useToast } from '../../components/Toast';

interface PricingForm {
  currency: string;
  soldStockBasis: 'sold' | 'stock';
  newUsedBasis: 'new' | 'used';
  cacheTtlHours: number;
}

const DEFAULTS: PricingForm = {
  currency: 'USD',
  soldStockBasis: 'sold',
  newUsedBasis: 'used',
  cacheTtlHours: 168,
};

interface SettingValue<T> { value: T; }

export function Pricing() {
  const toast = useToast();
  const [form, setForm] = useState<PricingForm>(DEFAULTS);

  const q = useQuery({
    queryKey: ['settings', 'pricing'],
    queryFn: () => api<SettingValue<PricingForm>>('/settings/pricing'),
  });

  useEffect(() => {
    if (q.data?.value) setForm({ ...DEFAULTS, ...q.data.value });
  }, [q.data]);

  const save = useMutation({
    mutationFn: (body: PricingForm) =>
      api('/settings/pricing', { method: 'PUT', body: { value: body } }),
    onSuccess: () => toast('success', 'Pricing saved'),
    onError: () => toast('error', 'Could not save pricing'),
  });

  function update<K extends keyof PricingForm>(key: K, value: PricingForm[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <Card title="Pricing" actions={<button className="primary" onClick={() => save.mutate(form)} disabled={save.isPending}>Save</button>}>
      <div className="form-grid">
        <div className="form-row">
          <label>Currency</label>
          <input value={form.currency} onChange={(e) => update('currency', e.target.value)} />
        </div>
        <div className="form-row">
          <label>Sold / Stock Basis</label>
          <select value={form.soldStockBasis} onChange={(e) => update('soldStockBasis', e.target.value as 'sold' | 'stock')}>
            <option value="sold">sold</option>
            <option value="stock">stock</option>
          </select>
        </div>
        <div className="form-row">
          <label>New / Used Basis</label>
          <select value={form.newUsedBasis} onChange={(e) => update('newUsedBasis', e.target.value as 'new' | 'used')}>
            <option value="new">new</option>
            <option value="used">used</option>
          </select>
        </div>
        <div className="form-row">
          <label>Cache TTL (hours)</label>
          <input type="number" min={1} value={form.cacheTtlHours} onChange={(e) => update('cacheTtlHours', Number(e.target.value))} />
        </div>
      </div>
    </Card>
  );
}

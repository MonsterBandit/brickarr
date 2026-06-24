import { useEffect, useState, useCallback } from 'react';

type ToastKind = 'info' | 'success' | 'error';
interface Toast { id: number; kind: ToastKind; message: string; }

let counter = 0;
const listeners = new Set<(t: Toast[]) => void>();
let toasts: Toast[] = [];

function push(kind: ToastKind, message: string) {
  const id = ++counter;
  toasts = [...toasts, { id, kind, message }];
  listeners.forEach((l) => l(toasts));
  setTimeout(() => {
    toasts = toasts.filter((t) => t.id !== id);
    listeners.forEach((l) => l(toasts));
  }, 3500);
}

export function useToast() {
  return useCallback(
    (kindOrMessage: ToastKind | string, maybeMessage?: string) => {
      if (maybeMessage === undefined) push('info', kindOrMessage);
      else push(kindOrMessage as ToastKind, maybeMessage);
    },
    [],
  );
}

export function ToastHost() {
  const [current, setCurrent] = useState<Toast[]>(toasts);
  useEffect(() => {
    listeners.add(setCurrent);
    return () => { listeners.delete(setCurrent); };
  }, []);
  return (
    <div className="toast-host">
      {current.map((t) => (
        <div key={t.id} className={`toast ${t.kind}`}>{t.message}</div>
      ))}
    </div>
  );
}

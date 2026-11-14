import { useMeta } from '../../hooks/useConstants';

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  const meta = useMeta();
  if (!meta.data) return null;
  return (
    <p
      className={`rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-slate-600 ${compact ? 'text-[11px]' : 'text-xs'}`}
    >
      <strong className="text-slate-700">Engineering disclaimer.</strong> {meta.data.disclaimer}
    </p>
  );
}

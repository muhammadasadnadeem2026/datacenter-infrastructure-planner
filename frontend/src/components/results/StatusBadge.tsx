import { STATUS_STYLES } from '../../constants/modules';

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.info;
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${s.cls}`}
    >
      <span aria-hidden>{s.icon}</span>
      {s.label}
    </span>
  );
}

import { useState, type ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  defaultOpen?: boolean;
  badge?: ReactNode;
  children: ReactNode;
}

export function Section({ title, description, defaultOpen = false, badge, children }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <svg
            className={`h-3.5 w-3.5 text-slate-400 transition-transform ${open ? 'rotate-90' : ''}`}
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden
          >
            <path d="M7 4l6 6-6 6V4z" />
          </svg>
          {title}
        </span>
        {badge}
      </button>
      {open && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3">
          {description && <p className="mb-3 text-xs text-slate-500">{description}</p>}
          {children}
        </div>
      )}
    </section>
  );
}

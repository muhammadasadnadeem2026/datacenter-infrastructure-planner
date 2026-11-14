import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

export function PageHeader({
  title,
  description,
  tabs,
  eyebrow = 'Engineering tool',
}: {
  title: string;
  description?: string;
  tabs?: { to: string; label: string }[];
  eyebrow?: string;
}) {
  return (
    <div className="mb-5">
      <div className="eyebrow">{eyebrow}</div>
      <h1 className="hero-title mt-1 text-3xl sm:text-4xl">{title}</h1>
      {description && <p className="mt-2 max-w-3xl text-sm text-slate-500">{description}</p>}
      {tabs && (
        <div className="mt-3 flex gap-1 overflow-x-auto border-b border-slate-200">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                `-mb-px whitespace-nowrap border-b-2 px-3 py-1.5 text-sm ${
                  isActive
                    ? 'border-accent-600 font-semibold text-accent-700'
                    : 'border-transparent text-slate-600'
                }`
              }
            >
              {t.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
      {children}
    </div>
  );
}

export function Loading({ label = 'Calculating…' }: { label?: string }) {
  return (
    <div className="animate-pulse rounded-md bg-surface px-3 py-6 text-center text-sm text-slate-500">
      {label}
    </div>
  );
}

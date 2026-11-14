import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { NAV_SECTIONS, titleForPath } from '../../constants/navigation';
import { useMeta } from '../../hooks/useConstants';
import { selectUnitSystem, useProjectStore } from '../../stores/projectStore';
import { useThemeStore } from '../../stores/themeStore';
import { BrandLockup } from './BrandLogo';
import { Icons } from './icons';

function UnitToggle() {
  const unit = useProjectStore(selectUnitSystem);
  const setUnitSystem = useProjectStore((s) => s.setUnitSystem);
  return (
    <div
      className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-xs"
      role="radiogroup"
      aria-label="Unit system"
    >
      {(['imperial', 'metric'] as const).map((u) => (
        <button
          key={u}
          type="button"
          role="radio"
          aria-checked={unit === u}
          onClick={() => setUnitSystem(u)}
          className={`rounded-md px-2.5 py-1 font-semibold capitalize transition ${
            unit === u ? 'bg-surface text-accent-700 shadow-card' : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          {u}
        </button>
      ))}
    </div>
  );
}

function ThemeToggle() {
  const { resolved, toggle } = useThemeStore();
  const dark = resolved === 'dark';
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={dark ? 'Light mode' : 'Dark mode'}
      className="relative flex h-8 w-14 shrink-0 items-center rounded-full border border-slate-200 bg-slate-100 px-1"
    >
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full bg-surface text-accent-600 shadow-card transition-transform duration-300 ${
          dark ? 'translate-x-6' : 'translate-x-0'
        }`}
      >
        {dark ? <Icons.moon width={14} height={14} /> : <Icons.sun width={14} height={14} />}
      </span>
    </button>
  );
}

/** Brand chrome: always deep ink in both themes (the white wordmark needs a dark surface). */
function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { pathname } = useLocation();
  const meta = useMeta();
  return (
    <div className="flex h-full flex-col bg-brand-navy text-[#C4D2E8]">
      <div className="px-5 pb-4 pt-6">
        <BrandLockup className="h-[18px] w-auto" />
        <div className="mt-4 text-[11px] font-bold uppercase tracking-[0.18em] text-[#6C7CD7]">HallPlan</div>
        <div className="text-xs font-light text-[#C4D2E8]/75">Data Center Infrastructure Planner</div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 pb-4" aria-label="Main">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <div className="px-2.5 pb-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#6C7CD7]">
              {section.title}
            </div>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = Icons[item.icon];
                const active = pathname === item.to || !!item.match?.includes(pathname);
                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      onClick={onNavigate}
                      aria-current={active ? 'page' : undefined}
                      className={`group relative flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors ${
                        active
                          ? 'bg-[#D98E1F]/20 font-semibold text-white'
                          : 'text-[#C4D2E8]/80 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      {active && (
                        <span
                          className="absolute left-0 top-1.5 h-[calc(100%-12px)] w-[3px] rounded-r bg-brand-lime"
                          aria-hidden
                        />
                      )}
                      <Icon
                        className={`transition-colors ${active ? 'text-[#4D8BFF]' : 'text-[#6C7CD7] group-hover:text-[#C4D2E8]'}`}
                      />
                      {item.label}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
      <div className="border-t border-white/10 px-5 py-3 text-[11px] text-[#C4D2E8]/60">
        Calculation engine {meta.data ? `v${meta.data.engine_version}` : '…'}
        <br />
        Planning estimates only
      </div>
    </div>
  );
}

export function AppLayout() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);

  return (
    <div className="min-h-screen bg-canvas text-slate-800">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <Sidebar />
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <button
            type="button"
            className="absolute inset-0 bg-[#09132B]/60 backdrop-blur-sm"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85vw] animate-fade-up shadow-lift">
            <Sidebar onNavigate={() => setOpen(false)} />
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-surface/85 backdrop-blur">
          <div className="mx-auto flex max-w-[1500px] items-center gap-3 px-4 py-2.5 sm:px-6">
            <button
              type="button"
              className="btn px-2 lg:hidden"
              aria-label="Open menu"
              onClick={() => setOpen(true)}
            >
              <Icons.menu />
            </button>
            <div className="min-w-0 flex-1">
              <div className="eyebrow">HallPlan</div>
              <div className="truncate text-sm font-semibold text-slate-800">{titleForPath(pathname)}</div>
            </div>
            <UnitToggle />
            <ThemeToggle />
          </div>
        </header>
        <main key={pathname} className="mx-auto max-w-[1500px] animate-fade-up px-4 py-5 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

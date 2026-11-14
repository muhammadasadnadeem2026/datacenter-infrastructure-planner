import { PageHeader } from '../components/layouts/PageHeader';
import { Disclaimer } from '../components/results/Disclaimer';
import { METHODOLOGY } from '../constants/methodology';

export function MethodologyPage() {
  return (
    <div className="grid gap-6 lg:grid-cols-[14rem_minmax(0,1fr)]">
      <nav className="hidden lg:block" aria-label="Methodology sections">
        <ul className="sticky top-28 space-y-1 text-sm">
          {METHODOLOGY.map((s) => (
            <li key={s.id}>
              <a href={`#${s.id}`} className="text-slate-600 hover:text-accent-700">
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="min-w-0 max-w-3xl">
        <PageHeader
          title="Methodology"
          description="Every formula used by the HallPlan engine. The backend calculation modules are the only executable implementation; the UI, reports and exports display their results."
        />
        <div className="space-y-4">
          {METHODOLOGY.map((s) => (
            <section key={s.id} id={s.id} className="scroll-mt-28 card p-4">
              <h2 className="text-base font-semibold text-slate-900">{s.title}</h2>
              <p className="mt-1 text-sm text-slate-600">{s.intro}</p>
              <dl className="mt-3 space-y-2">
                {s.equations.map((e) => (
                  <div key={e.name} className="grid gap-1 sm:grid-cols-[12rem_minmax(0,1fr)]">
                    <dt className="text-sm text-slate-500">{e.name}</dt>
                    <dd>
                      <code className="block overflow-x-auto rounded bg-slate-50 px-2 py-1 font-mono text-sm text-slate-900">
                        {e.eq}
                      </code>
                      {e.note && <p className="mt-0.5 text-xs text-slate-500">{e.note}</p>}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
          <Disclaimer />
        </div>
      </div>
    </div>
  );
}

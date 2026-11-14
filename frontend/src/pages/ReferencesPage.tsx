import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { PageHeader } from '../components/layouts/PageHeader';
import { Panel } from '../components/results/ResultsDashboard';
import { useCoolingClasses, useReceptacles, useReferences, useVoltageLevels } from '../hooks/useConstants';
import { formatNumber } from '../utils/format';

const th = 'px-2 py-1.5 text-left text-xs font-medium text-slate-500';
const td = 'px-2 py-1.5 text-sm text-slate-700';

export function ReferencesPage() {
  const refs = useReferences();
  const rec = useReceptacles();
  const cooling = useCoolingClasses();
  const volts = useVoltageLevels();
  const { hash } = useLocation();

  useEffect(() => {
    if (hash && refs.data)
      document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [hash, refs.data]);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Reference"
        description="Source documents, the receptacle library, cooling classes and voltage levels. A rule is never attributed to a standard unless the provision has been verified; unverified entries are marked as such."
      />
      <Panel title="References">
        <ul className="space-y-3">
          {(refs.data ?? []).map((r) => (
            <li
              key={r.id}
              id={r.id}
              className={`scroll-mt-28 rounded-md border p-3 ${hash === `#${r.id}` ? 'border-accent-500 bg-accent-50' : 'border-slate-200'}`}
            >
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="font-mono text-xs text-slate-400">[{r.id}]</span>
                <span className="text-sm font-semibold text-slate-800">{r.organization}</span>
                <span className="text-sm text-slate-700">— {r.document}</span>
              </div>
              <div className="mt-0.5 text-xs text-slate-500">
                Edition: {r.edition} · Section: {r.section}
              </div>
              <p className="mt-1 text-sm text-slate-600">{r.description}</p>
              <div className="mt-1 flex flex-wrap gap-3 text-xs">
                <span className={r.date_verified ? 'text-emerald-700' : 'text-amber-700'}>
                  {r.date_verified ? `Verified ${r.date_verified}` : `Status: ${r.verification_status}`}
                </span>
                {r.url && (
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-accent-600 underline"
                  >
                    Source
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="Receptacle library">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr className="border-b border-slate-200">
                <th className={th}>Name</th>
                <th className={th}>Voltage</th>
                <th className={th}>Amps</th>
                <th className={th}>Phase</th>
                <th className={th}>Nominal kVA</th>
                <th className={th}>Derate</th>
                <th className={th}>Usable kVA</th>
                <th className={th}>Description</th>
              </tr>
            </thead>
            <tbody>
              {(rec.data ?? []).map((r) => (
                <tr key={r.id} className="border-b border-slate-100">
                  <td className={td}>{r.name}</td>
                  <td className={`${td} font-mono`}>{r.voltage}</td>
                  <td className={`${td} font-mono`}>{r.amps}</td>
                  <td className={td}>{r.phase}</td>
                  <td className={`${td} font-mono`}>{formatNumber(r.nominal_kva)}</td>
                  <td className={`${td} font-mono`}>{r.continuous_derate}</td>
                  <td className={`${td} font-mono`}>{formatNumber(r.usable_kva)}</td>
                  <td className={`${td} text-xs text-slate-500`}>{r.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Cooling-density classes">
          <ul className="space-y-2 text-sm">
            {(cooling.data?.cooling_classes ?? []).map((c) => (
              <li key={c.id}>
                <span className="font-mono text-xs text-slate-500">
                  {c.min_kw}–{c.max_kw ?? '∞'} kW/rack
                </span>{' '}
                <strong className="text-slate-800">{c.name}.</strong>{' '}
                <span className="text-slate-600">{c.description}</span>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Distribution voltage levels">
          <ul className="space-y-1 text-sm">
            {(volts.data ?? []).map((v) => (
              <li key={v.id}>
                <span className="inline-block w-20 font-mono">{v.label}</span>
                <span className="mr-2 text-xs text-slate-400">{v.class}</span>
                <span className="text-slate-600">{v.typical_use}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

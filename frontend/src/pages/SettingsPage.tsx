import { PageHeader } from '../components/layouts/PageHeader';
import { Panel } from '../components/results/ResultsDashboard';
import { useMeta } from '../hooks/useConstants';
import { useProjectStore } from '../stores/projectStore';
import type { Mode, UnitSystem } from '../types/schemas';

const sel = 'rounded-md border border-slate-300 px-2 py-1.5 text-sm';

export function SettingsPage() {
  const { settings, updateSettings, setUnitSystem, clearDraft } = useProjectStore();
  const meta = useMeta();
  return (
    <div className="max-w-2xl space-y-4">
      <PageHeader title="Settings" description="Preferences are stored in this browser only." />
      <Panel title="Defaults">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm text-slate-700">
            <span className="mb-1 block text-xs font-medium text-slate-600">Unit system</span>
            <select
              className={sel}
              value={settings.defaultUnitSystem}
              onChange={(e) => setUnitSystem(e.target.value as UnitSystem)}
            >
              <option value="imperial">Imperial (°F, ft², BTU/hr, tons)</option>
              <option value="metric">Metric (°C, m², kW thermal)</option>
            </select>
          </label>
          <label className="text-sm text-slate-700">
            <span className="mb-1 block text-xs font-medium text-slate-600">
              Default design mode (new projects)
            </span>
            <select
              className={sel}
              value={settings.defaultMode}
              onChange={(e) => updateSettings({ defaultMode: e.target.value as Mode })}
            >
              <option value="quick">Quick</option>
              <option value="standard">Standard</option>
              <option value="engineering">Engineering</option>
            </select>
          </label>
          <label className="text-sm text-slate-700">
            <span className="mb-1 block text-xs font-medium text-slate-600">
              Recalculation delay while typing (ms)
            </span>
            <input
              type="number"
              min={0}
              max={2000}
              className={sel}
              value={settings.debounceMs}
              onChange={(e) => {
                const v = Number(e.target.value);
                if (Number.isFinite(v) && v >= 0 && v <= 2000) updateSettings({ debounceMs: v });
              }}
            />
          </label>
        </div>
      </Panel>
      <Panel title="Local data">
        <p className="mb-2 text-sm text-slate-600">
          The calculator keeps an unsaved draft in this browser. Saved projects live on the server.
        </p>
        <button
          type="button"
          className="rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
          onClick={() => window.confirm('Discard the local draft?') && clearDraft()}
        >
          Discard local draft
        </button>
      </Panel>
      <Panel title="About">
        <dl className="grid grid-cols-[10rem_1fr] gap-1 text-sm">
          <dt className="text-slate-500">Application</dt>
          <dd>{meta.data?.app ?? '…'}</dd>
          <dt className="text-slate-500">Engine version</dt>
          <dd className="font-mono">{meta.data?.engine_version ?? '…'}</dd>
          <dt className="text-slate-500">API</dt>
          <dd className="font-mono text-xs">
            {(import.meta.env.VITE_API_BASE_URL as string) || 'same origin (/api)'}
          </dd>
        </dl>
      </Panel>
    </div>
  );
}

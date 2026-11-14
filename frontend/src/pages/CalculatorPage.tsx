import { useEffect } from 'react';
import { CalculatorForm } from '../components/calculators/CalculatorForm';
import { ProjectBar } from '../components/calculators/ProjectBar';
import { ErrorNote, Loading } from '../components/layouts/PageHeader';
import { ResultsDashboard } from '../components/results/ResultsDashboard';
import { useFullCalculation } from '../hooks/useCalculation';
import { usePresets } from '../hooks/useConstants';
import { useProjectStore } from '../stores/projectStore';

export function CalculatorPage() {
  const inputs = useProjectStore((s) => s.inputs);
  const settings = useProjectStore((s) => s.settings);
  const openProject = useProjectStore((s) => s.openProject);
  const presets = usePresets();

  // First visit: start from the enterprise preset served by the backend.
  useEffect(() => {
    if (inputs || !presets.data) return;
    const p = presets.data.find((x) => x.id === 'enterprise') ?? presets.data[0];
    openProject(null, 'Untitled project', {
      ...p.inputs,
      mode: settings.defaultMode,
      unit_system: settings.defaultUnitSystem,
    });
  }, [inputs, presets.data, openProject, settings.defaultMode, settings.defaultUnitSystem]);

  const calc = useFullCalculation(inputs);
  const devices = (calc.data?.modules.it?.data.devices as { calculated_w: number }[] | undefined) ?? [];

  if (!inputs) {
    return presets.isError ? (
      <ErrorNote>Cannot reach the HallPlan API. Start the backend (see README) and reload.</ErrorNote>
    ) : (
      <Loading label="Loading presets…" />
    );
  }

  return (
    <div>
      <div className="mb-5">
        <div className="eyebrow">AI data center · power &amp; cooling</div>
        <h1 className="hero-title mt-1 text-3xl sm:text-4xl">
          Data Center <span className="font-semibold text-accent-600">Load Calculator</span>
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          Size IT, electrical, UPS, cooling, transformer, generator and BESS capacity from one authoritative
          engine. Every result shows its formula and substituted calculation.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="min-w-0 space-y-3">
          <ProjectBar result={calc.data} />
          <CalculatorForm initial={inputs} deviceWatts={devices.map((d) => d.calculated_w)} />
        </div>
        <div className="min-w-0">
          <div className="lg:sticky lg:top-[112px]">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700">Results</h2>
              <span className="text-xs text-slate-400">{calc.isFetching ? 'Recalculating…' : 'Live'}</span>
            </div>
            {calc.isError && <ErrorNote>{(calc.error as Error).message}</ErrorNote>}
            {calc.data ? (
              <div className={calc.isFetching ? 'opacity-70 transition-opacity' : ''}>
                <ResultsDashboard result={calc.data} unitSystem={inputs.unit_system} />
              </div>
            ) : (
              !calc.isError && <Loading />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

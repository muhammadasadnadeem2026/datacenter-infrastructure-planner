import { MODULE_ORDER, MODULE_TITLES } from '../../constants/modules';
import type { ModuleOut } from '../../types/api';
import { Section } from '../forms/Section';
import { StepRow } from './StepRow';

export function ModuleDetails({
  modules,
  openFirst = false,
}: {
  modules: Record<string, ModuleOut>;
  openFirst?: boolean;
}) {
  const keys = [
    ...MODULE_ORDER.filter((k) => k in modules),
    ...Object.keys(modules).filter((k) => !MODULE_ORDER.includes(k)),
  ];
  return (
    <div className="space-y-2">
      {keys.map((k, i) => (
        <Section
          key={k}
          title={MODULE_TITLES[k] ?? k}
          defaultOpen={openFirst && i === 0}
          badge={<span className="text-xs text-slate-400">{modules[k].steps.length} results</span>}
        >
          <ul className="divide-y divide-slate-100">
            {modules[k].steps.map((s) => (
              <StepRow key={s.key} step={s} />
            ))}
          </ul>
        </Section>
      ))}
    </div>
  );
}

export function AssumptionsList({ modules }: { modules: Record<string, ModuleOut> }) {
  const set = new Set<string>();
  Object.values(modules).forEach((m) => m.steps.forEach((s) => s.assumption && set.add(s.assumption)));
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
      {[...set].map((a) => (
        <li key={a}>{a}</li>
      ))}
    </ul>
  );
}

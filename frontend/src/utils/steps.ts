import type { ModuleOut, Step, ToolResponse } from '../types/api';

export function findStep(
  modules: Record<string, ModuleOut> | undefined,
  module: string,
  key: string,
): Step | undefined {
  return modules?.[module]?.steps.find((s) => s.key === key);
}

export function stepValue(res: ToolResponse | undefined, module: string, key: string) {
  return findStep(res?.modules, module, key)?.value;
}

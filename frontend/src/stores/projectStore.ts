/**
 * Global project state: the single ProjectInputs document plus the open project's identity.
 * Components read inputs from here; every result is fetched from the backend engine.
 */
import { create } from 'zustand';
import type { Mode, ProjectInputs, UnitSystem } from '../types/schemas';
import { safeStorage } from '../utils/storage';

const DRAFT_KEY = 'hallplan.draft.v1';
const SETTINGS_KEY = 'hallplan.settings.v1';

interface Draft {
  inputs: ProjectInputs;
  projectId: string | null;
  projectName: string;
}

export interface Settings {
  defaultMode: Mode;
  defaultUnitSystem: UnitSystem;
  debounceMs: number;
}

const defaultSettings: Settings = { defaultMode: 'standard', defaultUnitSystem: 'imperial', debounceMs: 300 };

interface ProjectState {
  inputs: ProjectInputs | null;
  /** Bumped whenever inputs are replaced from outside the form (preset, load, import). */
  revision: number;
  projectId: string | null;
  projectName: string;
  dirty: boolean;
  settings: Settings;
  setInputs: (inputs: ProjectInputs) => void;
  replaceInputs: (inputs: ProjectInputs) => void;
  openProject: (id: string | null, name: string, inputs: ProjectInputs) => void;
  setProjectMeta: (id: string | null, name: string) => void;
  markSaved: () => void;
  updateSettings: (patch: Partial<Settings>) => void;
  setUnitSystem: (u: UnitSystem) => void;
  clearDraft: () => void;
}

/** Unit system for display: the open project's, else the user default. */
export const selectUnitSystem = (s: ProjectState): UnitSystem =>
  s.inputs?.unit_system ?? s.settings.defaultUnitSystem;

const draft = safeStorage.get<Draft>(DRAFT_KEY);

function persist(s: Pick<ProjectState, 'inputs' | 'projectId' | 'projectName'>) {
  if (s.inputs)
    safeStorage.set(DRAFT_KEY, { inputs: s.inputs, projectId: s.projectId, projectName: s.projectName });
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  inputs: draft?.inputs ?? null,
  revision: 0,
  projectId: draft?.projectId ?? null,
  projectName: draft?.projectName ?? 'Untitled project',
  dirty: false,
  settings: { ...defaultSettings, ...(safeStorage.get<Partial<Settings>>(SETTINGS_KEY) ?? {}) },
  setInputs: (inputs) => {
    set({ inputs, dirty: true });
    persist(get());
  },
  replaceInputs: (inputs) => {
    set((s) => ({ inputs, revision: s.revision + 1, dirty: true }));
    persist(get());
  },
  openProject: (projectId, projectName, inputs) => {
    set((s) => ({ inputs, projectId, projectName, revision: s.revision + 1, dirty: false }));
    persist(get());
  },
  setProjectMeta: (projectId, projectName) => {
    set({ projectId, projectName });
    persist(get());
  },
  markSaved: () => set({ dirty: false }),
  updateSettings: (patch) => {
    const settings = { ...get().settings, ...patch };
    set({ settings });
    safeStorage.set(SETTINGS_KEY, settings);
  },
  setUnitSystem: (unit_system) => {
    const { inputs } = get();
    if (inputs) get().replaceInputs({ ...inputs, unit_system });
    get().updateSettings({ defaultUnitSystem: unit_system });
  },
  clearDraft: () => {
    safeStorage.remove(DRAFT_KEY);
    set((s) => ({
      inputs: null,
      projectId: null,
      projectName: 'Untitled project',
      revision: s.revision + 1,
    }));
  },
}));

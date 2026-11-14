import type {
  FullResponse,
  Meta,
  PresetMeta,
  ProjectRecord,
  ProjectSummary,
  Receptacle,
  Reference,
  ToolResponse,
} from '../types/api';
import type { ProjectInputs } from '../types/schemas';

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function detailToMessage(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail))
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) =>
        [d.loc?.filter((p) => p !== 'body').join('.'), d.msg].filter(Boolean).join(': '),
      )
      .join('; ');
  return 'Request failed';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      msg = detailToMessage((await res.json()).detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function requestBlob(path: string, body: unknown): Promise<Blob> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${res.statusText}`);
  return res.blob();
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) });

export const api = {
  meta: () => request<Meta>('/api/meta'),
  presets: () => request<PresetMeta[]>('/api/constants/presets'),
  receptacles: () => request<Receptacle[]>('/api/constants/receptacles'),
  references: () => request<Reference[]>('/api/constants/references'),
  coolingClasses: () =>
    request<{
      cooling_classes: {
        id: string;
        name: string;
        min_kw: number;
        max_kw: number | null;
        description: string;
      }[];
      thermal_tiers: { id: string; name: string; min_kw: number; max_kw: number | null }[];
    }>('/api/constants/cooling-classes'),
  voltageLevels: () =>
    request<{ id: string; voltage_v: number; label: string; class: string; typical_use: string }[]>(
      '/api/constants/voltage-levels',
    ),
  aiRacks: () =>
    request<{
      classes: {
        id: string;
        name: string;
        min_kw: number;
        max_kw: number | null;
        typical_kw: number;
        cooling_type: string;
      }[];
      equipment_references: Record<string, string | number | null>[];
    }>('/api/constants/ai-racks'),
  conversions: () =>
    request<
      { id: string; label: string; from_unit: string; to_unit: string; formula: string; needs: string[] }[]
    >('/api/constants/conversions'),

  calculateFull: (inputs: ProjectInputs) => post<FullResponse>('/api/calculate/full', inputs),
  calculateTool: <T = ToolResponse>(endpoint: string, body: unknown) =>
    post<T>(`/api/calculate/${endpoint}`, body),

  listProjects: () => request<ProjectSummary[]>('/api/projects'),
  getProject: (id: string) => request<ProjectRecord>(`/api/projects/${encodeURIComponent(id)}`),
  createProject: (name: string, inputs: ProjectInputs) =>
    post<ProjectRecord>('/api/projects', { name, inputs }),
  updateProject: (id: string, patch: { name?: string; inputs?: ProjectInputs }) =>
    request<ProjectRecord>(`/api/projects/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(patch),
    }),
  cloneProject: (id: string) => post<ProjectRecord>(`/api/projects/${encodeURIComponent(id)}/clone`, {}),
  recalculateProject: (id: string) =>
    post<ProjectRecord>(`/api/projects/${encodeURIComponent(id)}/recalculate`, {}),
  deleteProject: (id: string) =>
    request<void>(`/api/projects/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  exportPdf: (project_name: string, inputs: ProjectInputs) =>
    requestBlob('/api/export/pdf', { project_name, inputs }),
  exportXlsx: (project_name: string, inputs: ProjectInputs) =>
    requestBlob('/api/export/xlsx', { project_name, inputs }),
  exportCsv: (sheet: string, project_name: string, inputs: ProjectInputs) =>
    requestBlob(`/api/export/csv/${sheet}`, { project_name, inputs }),
};

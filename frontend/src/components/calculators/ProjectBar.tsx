import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { api } from '../../services/api';
import { useProjectStore } from '../../stores/projectStore';
import type { FullResponse } from '../../types/api';
import { projectInputsSchema } from '../../types/schemas';
import { downloadBlob, downloadText, readFileText, safeFilename } from '../../utils/download';

const btn = 'btn';
const primary = 'btn-primary';

const CSV_SHEETS = [
  ['inputs', 'Inputs'],
  ['results', 'Results'],
  ['devices', 'Device list'],
  ['racks', 'Rack summary'],
  ['capacity', 'Capacity table'],
  ['warnings', 'Warnings'],
  ['calculations', 'Calculations'],
] as const;

export function ProjectBar({ result }: { result?: FullResponse }) {
  const { inputs, projectId, projectName, dirty, setProjectMeta, markSaved, openProject } = useProjectStore();
  const qc = useQueryClient();
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const flash = (ok: boolean, text: string) => {
    setMsg({ ok, text });
    setTimeout(() => setMsg(null), 4000);
  };

  const save = useMutation({
    mutationFn: async (asNew: boolean) => {
      if (!inputs) throw new Error('No valid inputs to save');
      return projectId && !asNew
        ? api.updateProject(projectId, { name: projectName, inputs })
        : api.createProject(asNew && projectId ? `${projectName} (copy)` : projectName, inputs);
    },
    onSuccess: (p) => {
      setProjectMeta(p.id, p.name);
      markSaved();
      void qc.invalidateQueries({ queryKey: ['projects'] });
      flash(true, `Saved (engine v${p.calculator_version})`);
    },
    onError: (e: Error) => flash(false, e.message),
  });

  async function exportFile(kind: 'pdf' | 'xlsx' | string) {
    if (!inputs) return;
    setBusy(true);
    try {
      const base = safeFilename(projectName);
      if (kind === 'pdf') downloadBlob(await api.exportPdf(projectName, inputs), `${base}_report.pdf`);
      else if (kind === 'xlsx') downloadBlob(await api.exportXlsx(projectName, inputs), `${base}.xlsx`);
      else downloadBlob(await api.exportCsv(kind, projectName, inputs), `${base}_${kind}.csv`);
    } catch (e) {
      flash(false, (e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function exportJson() {
    if (!inputs) return;
    const doc = {
      format: 'hallplan-project',
      name: projectName,
      calculator_version: result?.engine_version,
      exported_at: new Date().toISOString(),
      inputs,
      results: result,
      warnings: result?.warnings,
    };
    downloadText(JSON.stringify(doc, null, 2), `${safeFilename(projectName)}.json`, 'application/json');
  }

  async function importJson(file: File) {
    try {
      const doc = JSON.parse(await readFileText(file));
      const parsed = projectInputsSchema.safeParse(doc.inputs ?? doc);
      if (!parsed.success)
        return flash(false, `Invalid project file: ${parsed.error.issues[0]?.message ?? 'schema mismatch'}`);
      openProject(
        null,
        typeof doc.name === 'string' ? doc.name : file.name.replace(/\.json$/i, ''),
        parsed.data,
      );
      flash(true, 'Imported. Results were recalculated by the current engine; save to store it.');
    } catch {
      flash(false, 'File is not valid JSON');
    }
  }

  return (
    <div className="card p-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          aria-label="Project name"
          value={projectName}
          onChange={(e) => setProjectMeta(projectId, e.target.value)}
          className="min-w-0 flex-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-sm font-medium focus:border-accent-500 focus:outline-none"
        />
        {dirty && <span className="text-xs text-amber-700">unsaved</span>}
        <button
          type="button"
          className={primary}
          disabled={!inputs || save.isPending}
          onClick={() => save.mutate(false)}
        >
          {projectId ? 'Save' : 'Save project'}
        </button>
        {projectId && (
          <button
            type="button"
            className={btn}
            disabled={!inputs || save.isPending}
            onClick={() => save.mutate(true)}
          >
            Save as copy
          </button>
        )}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button type="button" className={btn} disabled={!inputs || busy} onClick={() => exportFile('pdf')}>
          PDF report
        </button>
        <button type="button" className={btn} disabled={!inputs || busy} onClick={() => exportFile('xlsx')}>
          Excel (XLSX)
        </button>
        <select
          aria-label="Export CSV"
          className={btn}
          disabled={!inputs || busy}
          value=""
          onChange={(e) => e.target.value && exportFile(e.target.value)}
        >
          <option value="">CSV export…</option>
          {CSV_SHEETS.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
        <button type="button" className={btn} disabled={!inputs} onClick={exportJson}>
          Export JSON
        </button>
        <button type="button" className={btn} onClick={() => fileRef.current?.click()}>
          Import JSON
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".json,application/json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void importJson(f);
            e.target.value = '';
          }}
        />
        {msg && <span className={`text-xs ${msg.ok ? 'text-emerald-700' : 'text-red-600'}`}>{msg.text}</span>}
      </div>
    </div>
  );
}

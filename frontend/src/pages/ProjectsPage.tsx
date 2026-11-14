import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ErrorNote, Loading, PageHeader } from '../components/layouts/PageHeader';
import { useMeta } from '../hooks/useConstants';
import { api } from '../services/api';
import { useProjectStore } from '../stores/projectStore';
import type { ProjectSummary } from '../types/api';
import { projectInputsSchema } from '../types/schemas';
import { downloadText, readFileText, safeFilename } from '../utils/download';

const btn = 'btn';

export function ProjectsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const openProject = useProjectStore((s) => s.openProject);
  const meta = useMeta();
  const projects = useQuery({ queryKey: ['projects'], queryFn: api.listProjects });
  const [renaming, setRenaming] = useState<{ id: string; name: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const refresh = () => qc.invalidateQueries({ queryKey: ['projects'] });
  const onError = (e: Error) => setError(e.message);

  const rename = useMutation({
    mutationFn: (p: { id: string; name: string }) => api.updateProject(p.id, { name: p.name }),
    onSuccess: () => {
      setRenaming(null);
      void refresh();
    },
    onError,
  });
  const clone = useMutation({ mutationFn: api.cloneProject, onSuccess: refresh, onError });
  const remove = useMutation({ mutationFn: api.deleteProject, onSuccess: refresh, onError });
  const recalc = useMutation({ mutationFn: api.recalculateProject, onSuccess: refresh, onError });
  const create = useMutation({
    mutationFn: (p: { name: string; inputs: ReturnType<typeof projectInputsSchema.parse> }) =>
      api.createProject(p.name, p.inputs),
    onSuccess: refresh,
    onError,
  });

  async function open(p: ProjectSummary) {
    const rec = await api.getProject(p.id);
    openProject(rec.id, rec.name, rec.inputs);
    navigate('/calculator');
  }

  async function exportJson(p: ProjectSummary) {
    const rec = await api.getProject(p.id);
    downloadText(
      JSON.stringify({ format: 'hallplan-project', ...rec }, null, 2),
      `${safeFilename(rec.name)}.json`,
      'application/json',
    );
  }

  async function importJson(file: File) {
    try {
      const doc = JSON.parse(await readFileText(file));
      const parsed = projectInputsSchema.safeParse(doc.inputs ?? doc);
      if (!parsed.success) return setError(`Invalid project file: ${parsed.error.issues[0]?.message}`);
      create.mutate({
        name: typeof doc.name === 'string' ? doc.name : file.name.replace(/\.json$/i, ''),
        inputs: parsed.data,
      });
    } catch {
      setError('File is not valid JSON');
    }
  }

  return (
    <div>
      <PageHeader
        title="Saved Projects"
        description="Stored studies keep the engine version that produced them. Recalculate explicitly to move a study to the current engine."
      />
      <div className="mb-3 flex gap-2">
        <button type="button" className={btn} onClick={() => navigate('/calculator')}>
          + New from calculator
        </button>
        <button type="button" className={btn} onClick={() => fileRef.current?.click()}>
          Import JSON
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void importJson(f);
            e.target.value = '';
          }}
        />
      </div>
      {error && (
        <div className="mb-3">
          <ErrorNote>{error}</ErrorNote>
        </div>
      )}
      {projects.isLoading && <Loading label="Loading projects…" />}
      {projects.isError && <ErrorNote>{(projects.error as Error).message}</ErrorNote>}
      {projects.data && !projects.data.length && (
        <p className="text-sm text-slate-500">No saved projects yet. Use “Save project” on the calculator.</p>
      )}
      {!!projects.data?.length && (
        <div className="overflow-x-auto card">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Updated</th>
                <th className="px-3 py-2 font-medium">Engine</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {projects.data.map((p) => {
                const stale = meta.data && meta.data.engine_version !== p.calculator_version;
                return (
                  <tr key={p.id} className="border-b border-slate-100">
                    <td className="px-3 py-2">
                      {renaming?.id === p.id ? (
                        <form
                          className="flex gap-1"
                          onSubmit={(e) => {
                            e.preventDefault();
                            rename.mutate(renaming);
                          }}
                        >
                          <input
                            autoFocus
                            className="rounded border border-slate-300 px-2 py-0.5"
                            value={renaming.name}
                            onChange={(e) => setRenaming({ ...renaming, name: e.target.value })}
                          />
                          <button className={btn}>Save</button>
                        </form>
                      ) : (
                        <button
                          type="button"
                          className="font-medium text-accent-700 hover:underline"
                          onClick={() => void open(p)}
                        >
                          {p.name}
                        </button>
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{new Date(p.updated_at).toLocaleString()}</td>
                    <td className="px-3 py-2 font-mono text-xs">
                      v{p.calculator_version}
                      {stale && <span className="ml-1 text-amber-700">(older engine)</span>}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-right">
                      <div className="flex justify-end gap-1">
                        <button type="button" className={btn} onClick={() => void open(p)}>
                          Open
                        </button>
                        <button
                          type="button"
                          className={btn}
                          onClick={() => setRenaming({ id: p.id, name: p.name })}
                        >
                          Rename
                        </button>
                        <button type="button" className={btn} onClick={() => clone.mutate(p.id)}>
                          Clone
                        </button>
                        <button type="button" className={btn} onClick={() => void exportJson(p)}>
                          JSON
                        </button>
                        {stale && (
                          <button type="button" className={btn} onClick={() => recalc.mutate(p.id)}>
                            Recalculate
                          </button>
                        )}
                        <button
                          type="button"
                          className={`${btn} text-red-700`}
                          onClick={() =>
                            window.confirm(`Delete "${p.name}"? This cannot be undone.`) &&
                            remove.mutate(p.id)
                          }
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/** Builds a nested Zod schema from flat field definitions (used by standalone tool pages). */
import { z, type ZodTypeAny } from 'zod';
import type { FieldDef } from '../constants/fields';

export function fieldSchema(f: FieldDef): ZodTypeAny {
  if (f.type === 'checkbox') return z.boolean();
  if (f.type === 'select' || f.type === 'text') return z.string().min(1, `${f.label} is required`);
  let s = z.number({ invalid_type_error: `${f.label} must be a number` }).finite();
  if (f.integer) s = s.int(`${f.label} must be a whole number`);
  if (f.gt !== undefined) s = s.gt(f.gt, `${f.label} must be greater than ${f.gt}`);
  if (f.min !== undefined) s = s.min(f.min, `${f.label} must be ≥ ${f.min}`);
  if (f.max !== undefined) s = s.max(f.max, `${f.label} must be ≤ ${f.max}`);
  return f.optional ? s.nullable().optional() : s;
}

type Tree = { [k: string]: Tree | ZodTypeAny };

function toObject(tree: Tree): ZodTypeAny {
  const shape: Record<string, ZodTypeAny> = {};
  for (const [k, v] of Object.entries(tree)) shape[k] = v instanceof z.ZodType ? v : toObject(v as Tree);
  return z.object(shape);
}

export function buildSchema(fields: FieldDef[]): ZodTypeAny {
  const tree: Tree = {};
  for (const f of fields) {
    const keys = f.name.split('.');
    let cur = tree;
    keys.slice(0, -1).forEach((k) => {
      cur[k] = (cur[k] as Tree) ?? {};
      cur = cur[k] as Tree;
    });
    cur[keys[keys.length - 1]] = fieldSchema(f);
  }
  return toObject(tree);
}

/** Read / write nested values by dotted path (e.g. "ups.battery.enabled"). */

export function getPath(obj: unknown, path: string): unknown {
  return path
    .split('.')
    .reduce<unknown>(
      (o, k) => (o && typeof o === 'object' ? (o as Record<string, unknown>)[k] : undefined),
      obj,
    );
}

export function setPath<T extends Record<string, unknown>>(obj: T, path: string, value: unknown): T {
  const keys = path.split('.');
  const out: Record<string, unknown> = { ...obj };
  let cur = out;
  keys.forEach((k, i) => {
    if (i === keys.length - 1) {
      cur[k] = value;
    } else {
      const next = cur[k];
      cur[k] = next && typeof next === 'object' ? { ...(next as Record<string, unknown>) } : {};
      cur = cur[k] as Record<string, unknown>;
    }
  });
  return out as T;
}

// In-memory cache store (per server process).
const store = new Map<string, { value: unknown; expires: number }>();

export async function cached<T>(
  key: string,
  ttlSeconds: number,
  fn: () => Promise<T>,
): Promise<T> {
  const now = Date.now();
  const hit = store.get(key);
  if (hit && hit.expires > now) return hit.value as T;

  const value = await fn();
  store.set(key, { value, expires: now + ttlSeconds * 1000 });

  // Lazy cleanup when map grows too large
  if (store.size > 500) {
    for (const [k, v] of store) {
      if (v.expires <= now) store.delete(k);
    }
  }

  return value;
}

/** Remove all entries whose key starts with the given prefix. */
export function invalidateCache(prefix: string) {
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) store.delete(key);
  }
}

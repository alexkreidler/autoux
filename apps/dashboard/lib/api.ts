const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8766";

export const apiUrl = (path: string) => `${BASE}${path}`;

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path));
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

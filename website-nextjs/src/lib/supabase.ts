/**
 * Supabase client for server-side API routes.
 * Uses the service role key so it can read aggregate data.
 */

const SUPABASE_URL = process.env.SUPABASE_URL || "";
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || "";

export interface SupabaseQueryResult<T> {
  data: T | null;
  error: string | null;
}

export async function supabaseQuery<T>(
  table: string,
  params: Record<string, string> = {},
): Promise<SupabaseQueryResult<T>> {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return { data: null, error: "Supabase not configured" };
  }

  const url = new URL(`/rest/v1/${table}`, SUPABASE_URL);
  for (const [k, v] of Object.entries(params)) {
    url.searchParams.set(k, v);
  }

  const res = await fetch(url.toString(), {
    headers: {
      apikey: SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_KEY}`,
      "Content-Type": "application/json",
    },
    next: { revalidate: 60 },
  });

  if (!res.ok) {
    return { data: null, error: `Supabase ${res.status}: ${res.statusText}` };
  }

  const data = (await res.json()) as T;
  return { data, error: null };
}

export async function supabaseUpdate<T>(
  table: string,
  filters: Record<string, string>,
  body: Record<string, unknown>,
): Promise<SupabaseQueryResult<T>> {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return { data: null, error: "Supabase not configured" };
  }

  const url = new URL(`/rest/v1/${table}`, SUPABASE_URL);
  for (const [k, v] of Object.entries(filters)) {
    url.searchParams.set(k, v);
  }

  const res = await fetch(url.toString(), {
    method: "PATCH",
    headers: {
      apikey: SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "return=representation",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!res.ok) {
    return { data: null, error: `Supabase ${res.status}: ${res.statusText}` };
  }

  const data = (await res.json()) as T;
  return { data, error: null };
}

export async function supabaseInsert<T>(
  table: string,
  body: Record<string, unknown>,
): Promise<SupabaseQueryResult<T>> {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return { data: null, error: "Supabase not configured" };
  }

  const url = new URL(`/rest/v1/${table}`, SUPABASE_URL);

  const res = await fetch(url.toString(), {
    method: "POST",
    headers: {
      apikey: SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "return=representation",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (res.status === 409) {
    return { data: null, error: "duplicate" };
  }

  if (!res.ok) {
    return { data: null, error: `Supabase ${res.status}: ${res.statusText}` };
  }

  const data = (await res.json()) as T;
  return { data, error: null };
}

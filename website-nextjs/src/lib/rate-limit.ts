/**
 * Simple in-memory sliding-window rate limiter for API routes.
 * Keyed by IP address. Not shared across serverless instances,
 * but sufficient for MVP abuse prevention.
 */

const windows = new Map<string, number[]>();

const WINDOW_MS = 60_000;
const MAX_REQUESTS = 10;

export function isRateLimited(key: string): boolean {
  const now = Date.now();
  const cutoff = now - WINDOW_MS;
  const timestamps = (windows.get(key) || []).filter((t) => t > cutoff);

  if (timestamps.length >= MAX_REQUESTS) {
    windows.set(key, timestamps);
    return true;
  }

  timestamps.push(now);
  windows.set(key, timestamps);
  return false;
}

export function getClientIp(headers: Headers): string {
  return (
    headers.get("x-forwarded-for")?.split(",")[0].trim() ||
    headers.get("x-real-ip") ||
    "unknown"
  );
}

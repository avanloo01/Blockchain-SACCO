import { NextRequest, NextResponse } from "next/server";

const SUPABASE_URL = process.env.SUPABASE_URL ?? "";
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY ?? "";

/**
 * POST /api/checkout/link-order
 *
 * Called by the embedded checkout page once the Crossmint SDK creates a live
 * order.  Stores the Crossmint orderId in the `memo` column of the matching
 * BillingIntent row so the Telegram bot's /verify command can look it up.
 *
 * Body: { intentId: string; orderId: string }
 */
export async function POST(req: NextRequest) {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return NextResponse.json({ error: "Server not configured" }, { status: 500 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (
    typeof body !== "object" ||
    body === null ||
    typeof (body as Record<string, unknown>).intentId !== "string" ||
    typeof (body as Record<string, unknown>).orderId !== "string"
  ) {
    return NextResponse.json(
      { error: "Body must contain intentId and orderId strings" },
      { status: 400 }
    );
  }

  const { intentId, orderId } = body as { intentId: string; orderId: string };

  if (!intentId.trim() || !orderId.trim()) {
    return NextResponse.json({ error: "intentId and orderId must not be empty" }, { status: 400 });
  }

  // Look up the billing intent by its idempotency_key (= the intentId from the URL)
  const lookupUrl = new URL(`/rest/v1/billing_intents`, SUPABASE_URL);
  lookupUrl.searchParams.set("idempotency_key", `eq.${intentId.trim()}`);
  lookupUrl.searchParams.set("select", "id,memo");
  lookupUrl.searchParams.set("limit", "1");

  const headers = {
    apikey: SUPABASE_SERVICE_KEY,
    Authorization: `Bearer ${SUPABASE_SERVICE_KEY}`,
    "Content-Type": "application/json",
  };

  const lookupRes = await fetch(lookupUrl.toString(), { headers });
  if (!lookupRes.ok) {
    return NextResponse.json({ error: "Database lookup failed" }, { status: 502 });
  }

  const rows = (await lookupRes.json()) as Array<{ id: string; memo: string | null }>;
  if (!rows.length) {
    return NextResponse.json({ error: "Billing intent not found" }, { status: 404 });
  }

  const row = rows[0];

  // Patch the memo column with the Crossmint orderId
  const patchUrl = new URL(`/rest/v1/billing_intents`, SUPABASE_URL);
  patchUrl.searchParams.set("id", `eq.${row.id}`);

  const patchRes = await fetch(patchUrl.toString(), {
    method: "PATCH",
    headers: { ...headers, Prefer: "return=minimal" },
    body: JSON.stringify({ memo: orderId.trim() }),
  });

  if (!patchRes.ok) {
    return NextResponse.json({ error: "Database update failed" }, { status: 502 });
  }

  return NextResponse.json({ ok: true });
}

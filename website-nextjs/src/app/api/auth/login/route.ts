import { NextRequest, NextResponse } from "next/server";
import { randomBytes, createHash } from "crypto";
import { supabaseQuery, supabaseUpdate } from "@/lib/supabase";
import { isRateLimited, getClientIp } from "@/lib/rate-limit";
import { sendLoginEmail } from "@/lib/email";

const LOGIN_TOKEN_TTL_MS = 15 * 60 * 1000; // 15 minutes

function isSchemaError(error: string | null): boolean {
  if (!error) return false;
  return /(schema cache|column|does not exist|PGRST204)/i.test(error);
}

function generateLoginToken(): { raw: string; hashed: string } {
  const raw = randomBytes(32).toString("hex");
  const hashed = createHash("sha256").update(raw).digest("hex");
  return { raw, hashed };
}

export async function POST(req: NextRequest) {
  const ip = getClientIp(req.headers);
  if (isRateLimited(`login:${ip}`)) {
    return NextResponse.json(
      { error: "Too many requests, please try again later" },
      { status: 429 },
    );
  }

  const body = await req.json();
  const { email } = body as { email?: string };

  if (!email) {
    return NextResponse.json({ error: "Email is required" }, { status: 400 });
  }

  // Only allow existing members to log in.
  const { data: members } = await supabaseQuery<{ id: string; email: string }[]>(
    "members",
    { select: "id,email", email: `eq.${email}`, limit: "1" },
  );

  if (!members || members.length === 0) {
    // Return the same response as a found member to avoid email enumeration.
    return NextResponse.json({ ok: true });
  }

  const member = members[0];
  const { raw: token, hashed } = generateLoginToken();
  const expiresAt = new Date(Date.now() + LOGIN_TOKEN_TTL_MS).toISOString();

  const { error: updateError } = await supabaseUpdate(
    "members",
    { id: `eq.${member.id}` },
    { login_token: hashed, login_token_expires_at: expiresAt },
  );

  if (updateError && isSchemaError(updateError)) {
    console.error(
      "Login token columns missing from members schema; email login unavailable",
      updateError,
    );
    return NextResponse.json(
      { error: "Email login is not yet configured — please contact support" },
      { status: 503 },
    );
  }

  if (updateError) {
    console.error("Failed to store login token", { email, updateError });
    return NextResponse.json(
      { error: "Failed to send login link" },
      { status: 500 },
    );
  }

  const baseUrl = process.env.NEXTAUTH_URL || "http://localhost:3000";
  const loginUrl = `${baseUrl}/login/verify?token=${token}&email=${encodeURIComponent(email)}`;
  const emailResult = await sendLoginEmail(email, loginUrl);

  if (!emailResult.success) {
    console.error("Failed to send login email:", emailResult.error);
  }

  return NextResponse.json({ ok: true });
}

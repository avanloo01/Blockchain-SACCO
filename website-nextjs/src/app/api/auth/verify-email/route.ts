import { NextRequest, NextResponse } from "next/server";
import { createHash } from "crypto";
import { supabaseQuery, supabaseUpdate } from "@/lib/supabase";

interface MemberRow {
  id: string;
  email_verified: boolean;
}

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token");
  const email = req.nextUrl.searchParams.get("email");

  if (!token || !email) {
    return NextResponse.json(
      { error: "Missing token or email" },
      { status: 400 },
    );
  }

  const hashed = createHash("sha256").update(token).digest("hex");

  const { data: members } = await supabaseQuery<MemberRow[]>("members", {
    select: "id,email_verified",
    email: `eq.${email}`,
    email_verification_token: `eq.${hashed}`,
    limit: "1",
  });

  if (!members || members.length === 0) {
    return NextResponse.json(
      { error: "Invalid or expired verification link" },
      { status: 400 },
    );
  }

  if (members[0].email_verified) {
    return NextResponse.redirect(
      new URL("/onboarding?verified=1", req.nextUrl.origin),
    );
  }

  await supabaseUpdate("members", { id: `eq.${members[0].id}` }, {
    email_verified: true,
    email_verification_token: null,
  });

  return NextResponse.redirect(
    new URL("/onboarding?verified=1", req.nextUrl.origin),
  );
}

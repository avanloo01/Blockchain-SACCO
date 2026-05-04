import { NextRequest, NextResponse } from "next/server";
import { randomBytes, createHash, randomUUID } from "crypto";
import { supabaseInsert } from "@/lib/supabase";
import { isRateLimited, getClientIp } from "@/lib/rate-limit";
import { sendVerificationEmail } from "@/lib/email";

interface MemberRow {
  id: string;
  email: string;
  phone: string;
  wallet_address: string | null;
}

function isLegacyMembersSchemaError(error: string | null): boolean {
  if (!error) {
    return false;
  }

  return /(schema cache|column|does not exist|PGRST204)/i.test(error);
}

function generateVerificationToken(): { raw: string; hashed: string } {
  const raw = randomBytes(32).toString("hex");
  const hashed = createHash("sha256").update(raw).digest("hex");
  return { raw, hashed };
}

export async function POST(req: NextRequest) {
  const ip = getClientIp(req.headers);
  if (isRateLimited(`signup:${ip}`)) {
    return NextResponse.json(
      { error: "Too many requests, please try again later" },
      { status: 429 },
    );
  }

  const body = await req.json();
  const { email, phone, walletAddress } = body as {
    email?: string;
    phone?: string;
    walletAddress?: string;
  };

  if (!email || !phone) {
    return NextResponse.json(
      { error: "Email and phone are required" },
      { status: 400 },
    );
  }

  const { raw: token, hashed } = generateVerificationToken();
  const memberId = randomUUID();
  const updatedAt = new Date().toISOString();

  const baseMember = {
    id: memberId,
    email,
    phone,
    wallet_address: walletAddress || null,
    display_name: email.split("@")[0],
    updated_at: updatedAt,
  };

  let verificationEnabled = true;
  let { data, error } = await supabaseInsert<MemberRow[]>("members", {
    ...baseMember,
    email_verification_token: hashed,
  });

  if (error && isLegacyMembersSchemaError(error)) {
    console.warn(
      "Signup insert failed with verification token; retrying against legacy members schema",
      error,
    );
    verificationEnabled = false;
    ({ data, error } = await supabaseInsert<MemberRow[]>("members", baseMember));
  }

  if (error === "duplicate") {
    return NextResponse.json(
      { error: "An account with this email already exists" },
      { status: 409 },
    );
  }

  if (error || !data || data.length === 0) {
    console.error("Signup failed to create member", {
      email,
      error,
      verificationEnabled,
    });
    return NextResponse.json(
      { error: "Failed to create account" },
      { status: 500 },
    );
  }

  // Send verification email via Resend.
  if (verificationEnabled) {
    const verifyUrl = `${process.env.NEXTAUTH_URL || "http://localhost:3000"}/api/auth/verify-email?token=${token}&email=${encodeURIComponent(email)}`;
    const emailResult = await sendVerificationEmail(email, verifyUrl);

    if (!emailResult.success) {
      console.error("Failed to send verification email:", emailResult.error);
    }
  } else {
    console.warn(
      "Signup succeeded using legacy members schema fallback; email verification was skipped",
      { email },
    );
  }

  return NextResponse.json({
    ok: true,
    email,
    walletAddress: walletAddress ?? null,
  });
}

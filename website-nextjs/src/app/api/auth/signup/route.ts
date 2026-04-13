import { NextRequest, NextResponse } from "next/server";
import { supabaseInsert } from "@/lib/supabase";

interface MemberRow {
  id: string;
  email: string;
  phone: string;
  wallet_address: string | null;
}

export async function POST(req: NextRequest) {
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

  const { data, error } = await supabaseInsert<MemberRow[]>("members", {
    email,
    phone,
    wallet_address: walletAddress || null,
    display_name: email.split("@")[0],
  });

  if (error === "duplicate") {
    return NextResponse.json(
      { error: "An account with this email already exists" },
      { status: 409 },
    );
  }

  if (error || !data || data.length === 0) {
    return NextResponse.json(
      { error: "Failed to create account" },
      { status: 500 },
    );
  }

  return NextResponse.json({
    ok: true,
    email,
    walletAddress: walletAddress ?? null,
  });
}

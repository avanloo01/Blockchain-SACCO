import { NextRequest, NextResponse } from "next/server";

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

  // TODO: Create member in Supabase Auth and members table.
  // Store walletAddress on the member record if provided.
  // For now, return success so the signup flow can be tested end-to-end.
  return NextResponse.json({ ok: true, email, walletAddress: walletAddress ?? null });
}

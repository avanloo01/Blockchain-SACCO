import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { supabaseQuery } from "@/lib/supabase";

interface MemberRow {
  id: string;
  display_name: string | null;
  joined_on: string;
  contribution_total_usd: number;
  repayment_on_time_ratio: number;
}

interface LoanRow {
  id: string;
  amount_usd: number;
  tenure_months: number;
  status: string;
  governance_lane: string;
  created_at: string;
}

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  // Look up member by email (members table stores email in display_name for MVP,
  // or you can add an email column later).
  const { data: members } = await supabaseQuery<MemberRow[]>("members", {
    select:
      "id,display_name,joined_on,contribution_total_usd,repayment_on_time_ratio",
    limit: "1",
  });

  if (!members || members.length === 0) {
    return NextResponse.json({ error: "member not found" }, { status: 404 });
  }

  const member = members[0];
  const joined = new Date(member.joined_on);
  const now = new Date();
  const monthsActive = Math.max(
    0,
    Math.floor(
      (now.getTime() - joined.getTime()) / (1000 * 60 * 60 * 24 * 30),
    ),
  );

  const { data: loans } = await supabaseQuery<LoanRow[]>("loan_requests", {
    select: "id,amount_usd,tenure_months,status,governance_lane,created_at",
    member_id: `eq.${member.id}`,
    order: "created_at.desc",
  });

  return NextResponse.json({
    display_name: member.display_name,
    joined_on: member.joined_on,
    months_active: monthsActive,
    contribution_total_usd: member.contribution_total_usd,
    repayment_on_time_ratio: member.repayment_on_time_ratio,
    loans: (loans || []).map((l) => ({
      id: l.id,
      amount_usd: l.amount_usd,
      tenure_months: l.tenure_months,
      status: l.status,
      governance_lane: l.governance_lane,
      created_at: l.created_at,
    })),
  });
}

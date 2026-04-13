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

interface BillingRow {
  id: string;
  amount_usd: number;
  service_fee_usd: number;
  net_pool_amount_usd: number;
  status: string;
  created_at: string;
}

interface RepaymentRow {
  id: string;
  amount_usd: number;
  due_on: string;
  paid_on: string | null;
  status: string;
}

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  // Look up member by email from the authenticated session.
  const { data: members } = await supabaseQuery<MemberRow[]>("members", {
    select:
      "id,display_name,joined_on,contribution_total_usd,repayment_on_time_ratio",
    email: `eq.${session.user.email}`,
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

  const [{ data: loans }, { data: contributions }, { data: repayments }] =
    await Promise.all([
      supabaseQuery<LoanRow[]>("loan_requests", {
        select:
          "id,amount_usd,tenure_months,status,governance_lane,created_at",
        member_id: `eq.${member.id}`,
        order: "created_at.desc",
      }),
      supabaseQuery<BillingRow[]>("billing_intents", {
        select:
          "id,amount_usd,service_fee_usd,net_pool_amount_usd,status,created_at",
        member_id: `eq.${member.id}`,
        order: "created_at.desc",
        limit: "50",
      }),
      supabaseQuery<RepaymentRow[]>("repayment_schedules", {
        select: "id,amount_usd,due_on,paid_on,status",
        member_id: `eq.${member.id}`,
        order: "due_on.asc",
      }),
    ]);

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
    contributions: (contributions || []).map((c) => ({
      id: c.id,
      amount_usd: c.amount_usd,
      service_fee_usd: c.service_fee_usd,
      net_pool_amount_usd: c.net_pool_amount_usd,
      status: c.status,
      created_at: c.created_at,
    })),
    repayments: (repayments || []).map((r) => ({
      id: r.id,
      amount_usd: r.amount_usd,
      due_on: r.due_on,
      paid_on: r.paid_on,
      status: r.status,
    })),
  });
}

import { NextResponse } from "next/server";
import { supabaseQuery } from "@/lib/supabase";

interface Member {
  contribution_total_usd: number;
}

interface Loan {
  amount_usd: number;
  status: string;
}

interface Repayment {
  status: string;
}

export async function GET() {
  const [membersRes, loansRes, repaymentsRes] = await Promise.all([
    supabaseQuery<Member[]>("members", { select: "contribution_total_usd" }),
    supabaseQuery<Loan[]>("loan_requests", { select: "amount_usd,status" }),
    supabaseQuery<Repayment[]>("repayment_schedules", { select: "status" }),
  ]);

  const members = membersRes.data || [];
  const loans = loansRes.data || [];
  const repayments = repaymentsRes.data || [];

  const totalContributed = members.reduce(
    (sum, m) => sum + m.contribution_total_usd,
    0,
  );
  const activeLoans = loans.filter((l) =>
    ["pending", "approved"].includes(l.status),
  );
  const totalLent = activeLoans.reduce((sum, l) => sum + l.amount_usd, 0);
  const poolBalance = totalContributed - totalLent;
  const utilization =
    totalContributed > 0 ? (totalLent / totalContributed) * 100 : 0;

  const totalRepayments = repayments.length;
  const paidOnTime = repayments.filter((r) => r.status === "paid").length;
  const repaymentPercent =
    totalRepayments > 0 ? (paidOnTime / totalRepayments) * 100 : 100;

  return NextResponse.json({
    pool_balance_usd: poolBalance,
    total_contributed_usd: totalContributed,
    total_lent_usd: totalLent,
    utilization_percent: utilization,
    member_count: members.length,
    active_loans: activeLoans.length,
    repayment_on_time_percent: repaymentPercent,
  });
}

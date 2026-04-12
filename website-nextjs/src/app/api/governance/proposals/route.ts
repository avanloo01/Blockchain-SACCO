import { NextResponse } from "next/server";
import { supabaseQuery } from "@/lib/supabase";

interface LoanRow {
  id: string;
  amount_usd: number;
  governance_lane: string;
  status: string;
  reason: string | null;
  created_at: string;
  member_id: string;
}

interface Proposal {
  id: string;
  title: string;
  amount_usd: number;
  status: "active" | "passed" | "rejected";
  votes_for: number;
  votes_against: number;
  created_at: string;
  description?: string;
}

export async function GET() {
  // Governance proposals are loan requests that went to the "vote" lane.
  const { data, error } = await supabaseQuery<LoanRow[]>("loan_requests", {
    select: "id,amount_usd,governance_lane,status,reason,created_at,member_id",
    governance_lane: "eq.vote",
    order: "created_at.desc",
    limit: "50",
  });

  if (error || !data) {
    return NextResponse.json([], { status: 200 });
  }

  const proposals: Proposal[] = data.map((row) => {
    let status: Proposal["status"] = "active";
    if (row.status === "approved") status = "passed";
    else if (row.status === "rejected" || row.status === "declined")
      status = "rejected";

    return {
      id: row.id,
      title: `Loan request: $${row.amount_usd.toFixed(2)}`,
      amount_usd: row.amount_usd,
      status,
      votes_for: 0,
      votes_against: 0,
      created_at: row.created_at,
      description: row.reason || undefined,
    };
  });

  return NextResponse.json(proposals);
}

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

interface VoteRow {
  loan_request_id: string;
  vote: string;
}

export async function GET() {
  // Governance proposals are loan requests that went to the "vote" lane.
  const { data, error } = await supabaseQuery<LoanRow[]>("loan_requests", {
    select: "id,amount_usd,governance_lane,status,reason,created_at,member_id",
    governance_lane: "eq.vote",
    order: "created_at.desc",
    limit: "50",
  });

  if (error || !data || data.length === 0) {
    return NextResponse.json([], { status: 200 });
  }

  // Fetch vote tallies for all returned proposals in one query.
  const loanIds = data.map((r) => r.id);
  const { data: votes } = await supabaseQuery<VoteRow[]>("governance_votes", {
    select: "loan_request_id,vote",
    loan_request_id: `in.(${loanIds.join(",")})`,
  });

  const tallies: Record<string, { yes: number; no: number }> = {};
  for (const v of votes || []) {
    if (!tallies[v.loan_request_id]) {
      tallies[v.loan_request_id] = { yes: 0, no: 0 };
    }
    if (v.vote === "yes") tallies[v.loan_request_id].yes++;
    else if (v.vote === "no") tallies[v.loan_request_id].no++;
  }

  const proposals: Proposal[] = data.map((row) => {
    let status: Proposal["status"] = "active";
    if (row.status === "approved") status = "passed";
    else if (row.status === "rejected" || row.status === "declined")
      status = "rejected";

    const tally = tallies[row.id] || { yes: 0, no: 0 };

    return {
      id: row.id,
      title: `Loan request: $${row.amount_usd.toFixed(2)}`,
      amount_usd: row.amount_usd,
      status,
      votes_for: tally.yes,
      votes_against: tally.no,
      created_at: row.created_at,
      description: row.reason || undefined,
    };
  });

  return NextResponse.json(proposals);
}

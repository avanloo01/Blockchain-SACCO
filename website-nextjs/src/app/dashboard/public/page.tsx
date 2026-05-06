import Link from "next/link";
import { StatCard } from "@/components/StatCard";
import { supabaseQuery } from "@/lib/supabase";
import styles from "../dashboard.module.css";

interface MemberRow {
  contribution_total_usd: number;
}

interface LoanRow {
  amount_usd: number;
  status: string;
}

interface RepaymentRow {
  status: string;
}

interface PoolStats {
  pool_balance_usd: number;
  total_contributed_usd: number;
  total_lent_usd: number;
  utilization_percent: number;
  member_count: number;
  active_loans: number;
  repayment_on_time_percent: number;
}

async function fetchPoolStats(): Promise<PoolStats> {
  const [membersRes, loansRes, repaymentsRes] = await Promise.all([
    supabaseQuery<MemberRow[]>("members", { select: "contribution_total_usd" }),
    supabaseQuery<LoanRow[]>("loan_requests", { select: "amount_usd,status" }),
    supabaseQuery<RepaymentRow[]>("repayment_schedules", { select: "status" }),
  ]);

  const members = membersRes.data || [];
  const loans = loansRes.data || [];
  const repayments = repaymentsRes.data || [];

  const totalContributed = members.reduce((sum, m) => sum + m.contribution_total_usd, 0);
  const activeLoans = loans.filter((l) => ["pending", "approved"].includes(l.status));
  const totalLent = activeLoans.reduce((sum, l) => sum + l.amount_usd, 0);
  const poolBalance = totalContributed - totalLent;
  const utilization = totalContributed > 0 ? (totalLent / totalContributed) * 100 : 0;

  const totalRepayments = repayments.length;
  const paidOnTime = repayments.filter((r) => r.status === "paid").length;
  const repaymentPercent = totalRepayments > 0 ? (paidOnTime / totalRepayments) * 100 : 100;

  return {
    pool_balance_usd: poolBalance,
    total_contributed_usd: totalContributed,
    total_lent_usd: totalLent,
    utilization_percent: utilization,
    member_count: members.length,
    active_loans: activeLoans.length,
    repayment_on_time_percent: repaymentPercent,
  };
}

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default async function PublicDashboard() {
  const stats = await fetchPoolStats();

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div className={styles.header}>
          <h2>Pool Dashboard</h2>
          <p className={styles.headerSub}>
            Public aggregate metrics for the Blockchain SACCO pool. No personal
            data is exposed.
          </p>
        </div>
        <Link href="/dashboard/member" className="btn btn-primary">
          My Dashboard
        </Link>
      </div>

      <div className={styles.grid}>
        <StatCard
          label="Pool Balance"
          value={`$${fmt(stats.pool_balance_usd)}`}
          sub="Total available funds"
        />
        <StatCard
          label="Total Contributed"
          value={`$${fmt(stats.total_contributed_usd)}`}
          sub="Lifetime member deposits"
        />
        <StatCard
          label="Total Lent"
          value={`$${fmt(stats.total_lent_usd)}`}
          sub="Outstanding principal"
        />
        <StatCard
          label="Utilization"
          value={`${stats.utilization_percent.toFixed(1)}%`}
          sub="Cap: 60%"
        />
      </div>

      <div className={styles.grid}>
        <StatCard label="Members" value={String(stats.member_count)} />
        <StatCard label="Active Loans" value={String(stats.active_loans)} />
        <StatCard
          label="On-time Repayment"
          value={`${stats.repayment_on_time_percent.toFixed(0)}%`}
        />
      </div>

      <p className={styles.timestamp}>
        Data refreshes every 5 minutes. Individual member details are private.
      </p>
    </div>
  );
}

import { supabaseQuery } from "@/lib/supabase";
import styles from "./page.module.css";

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

interface LoanRow {
  id: string;
  amount_usd: number;
  governance_lane: string;
  status: string;
  reason: string | null;
  created_at: string;
}

async function fetchProposals(): Promise<Proposal[]> {
  const { data } = await supabaseQuery<LoanRow[]>("loan_requests", {
    select: "id,amount_usd,governance_lane,status,reason,created_at",
    governance_lane: "eq.vote",
    order: "created_at.desc",
    limit: "50",
  });

  if (!data) {
    return [];
  }

  return data.map((row) => {
    let status: Proposal["status"] = "active";
    if (row.status === "approved") status = "passed";
    else if (row.status === "rejected" || row.status === "declined") {
      status = "rejected";
    }

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
}

function statusClass(status: string) {
  if (status === "passed") return styles.badgePassed;
  if (status === "rejected") return styles.badgeRejected;
  return styles.badgeActive;
}

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default async function GovernancePage() {
  const proposals = await fetchProposals();

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2>Governance</h2>
        <p className={styles.headerSub}>
          Loan requests above $100 require a community vote. Results are
          recorded on-chain for transparency.
        </p>
      </div>

      {proposals.length === 0 ? (
        <p className={styles.empty}>
          No governance proposals yet. Proposals are created automatically when
          a member requests a loan above the governance threshold.
        </p>
      ) : (
        <div className={styles.list}>
          {proposals.map((p) => (
            <div key={p.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>{p.title}</span>
                <span className={`${styles.badge} ${statusClass(p.status)}`}>
                  {p.status}
                </span>
              </div>
              <div className={styles.meta}>
                <span>Amount: ${fmt(p.amount_usd)}</span>
                <span>
                  For: {p.votes_for} / Against: {p.votes_against}
                </span>
                <span>{new Date(p.created_at).toLocaleDateString()}</span>
              </div>
              {p.description && <p className={styles.desc}>{p.description}</p>}
            </div>
          ))}
        </div>
      )}

      <div className={styles.note}>
        Voting happens in the Telegram bot. Use <code>/vote</code> to
        participate in active proposals.
      </div>
    </div>
  );
}

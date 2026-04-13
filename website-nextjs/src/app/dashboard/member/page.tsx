"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/StatCard";
import styles from "../dashboard.module.css";

interface MemberData {
  display_name: string | null;
  joined_on: string;
  months_active: number;
  contribution_total_usd: number;
  repayment_on_time_ratio: number;
  loans: {
    id: string;
    amount_usd: number;
    tenure_months: number;
    status: string;
    governance_lane: string;
    created_at: string;
  }[];
  contributions: {
    id: string;
    amount_usd: number;
    service_fee_usd: number;
    net_pool_amount_usd: number;
    status: string;
    created_at: string;
  }[];
  repayments: {
    id: string;
    amount_usd: number;
    due_on: string;
    paid_on: string | null;
    status: string;
  }[];
}

function fmt(n: number) {
  return n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function statusClass(status: string) {
  if (status === "approved") return styles.badgeApproved;
  if (status === "rejected" || status === "declined") return styles.badgeRejected;
  return styles.badgePending;
}

export default function MemberDashboard() {
  const [data, setData] = useState<MemberData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/member")
      .then((res) => {
        if (res.status === 401) throw new Error("unauthorized");
        if (!res.ok) throw new Error("failed");
        return res.json();
      })
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className={styles.page}>
        <p style={{ color: "var(--foreground-muted)" }}>Loading...</p>
      </div>
    );
  }

  if (error === "unauthorized" || !data) {
    return (
      <div className={styles.page}>
        <h2>Sign in to view your dashboard</h2>
        <p className={styles.headerSub} style={{ marginBottom: "1.5rem" }}>
          You need an account to access your personal contribution and loan
          history.
        </p>
        <Link href="/signup" className="btn btn-primary">
          Sign Up
        </Link>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2>My Dashboard</h2>
        <p className={styles.headerSub}>
          {data.display_name || "Member"} · joined{" "}
          {new Date(data.joined_on).toLocaleDateString()}
        </p>
      </div>

      <div className={styles.grid}>
        <StatCard
          label="Total Contributed"
          value={`$${fmt(data.contribution_total_usd)}`}
        />
        <StatCard
          label="Months Active"
          value={String(data.months_active)}
        />
        <StatCard
          label="On-time Repayment"
          value={`${(data.repayment_on_time_ratio * 100).toFixed(0)}%`}
        />
      </div>

      <div className={styles.section}>
        <h3 style={{ marginBottom: "1rem" }}>Loan History</h3>
        {data.loans.length === 0 ? (
          <p style={{ color: "var(--foreground-muted)" }}>
            No loan requests yet. Use <code>/loan_request</code> in the Telegram
            bot to apply.
          </p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Amount</th>
                <th>Tenure</th>
                <th>Lane</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.loans.map((loan) => (
                <tr key={loan.id}>
                  <td>${fmt(loan.amount_usd)}</td>
                  <td>{loan.tenure_months}mo</td>
                  <td>{loan.governance_lane}</td>
                  <td>
                    <span
                      className={`${styles.badge} ${statusClass(loan.status)}`}
                    >
                      {loan.status}
                    </span>
                  </td>
                  <td>{new Date(loan.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className={styles.section}>
        <h3 style={{ marginBottom: "1rem" }}>Contribution History</h3>
        {data.contributions.length === 0 ? (
          <p style={{ color: "var(--foreground-muted)" }}>
            No contributions yet. Use <code>/contribute</code> in the Telegram
            bot to make your first deposit.
          </p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Amount</th>
                <th>Fee</th>
                <th>Net to Pool</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.contributions.map((c) => (
                <tr key={c.id}>
                  <td>${fmt(c.amount_usd)}</td>
                  <td>${fmt(c.service_fee_usd)}</td>
                  <td>${fmt(c.net_pool_amount_usd)}</td>
                  <td>
                    <span
                      className={`${styles.badge} ${statusClass(c.status)}`}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td>{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className={styles.section}>
        <h3 style={{ marginBottom: "1rem" }}>Repayment Schedule</h3>
        {data.repayments.length === 0 ? (
          <p style={{ color: "var(--foreground-muted)" }}>
            No repayments scheduled.
          </p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Amount</th>
                <th>Due</th>
                <th>Paid</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.repayments.map((r) => (
                <tr key={r.id}>
                  <td>${fmt(r.amount_usd)}</td>
                  <td>{new Date(r.due_on).toLocaleDateString()}</td>
                  <td>
                    {r.paid_on
                      ? new Date(r.paid_on).toLocaleDateString()
                      : "\u2014"}
                  </td>
                  <td>
                    <span
                      className={`${styles.badge} ${statusClass(r.status)}`}
                    >
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

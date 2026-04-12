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
    </div>
  );
}

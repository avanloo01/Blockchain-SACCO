import Link from "next/link";
import styles from "./page.module.css";

export default function Home() {
  return (
    <>
      <section className={styles.hero}>
        <span className={styles.badge}>Powered by Solana + USDC</span>
        <h1 className={styles.headline}>
          Community savings, transparent and on-chain
        </h1>
        <p className={styles.sub}>
          Blockchain SACCO lets members contribute monthly, access fair loans,
          and track every dollar through a public transparency dashboard.
        </p>
        <div className={styles.cta}>
          <Link href="/signup" className="btn btn-primary">
            Create Account
          </Link>
          <Link href="/dashboard/public" className="btn btn-outline">
            View Dashboard
          </Link>
        </div>
      </section>

      <section className="container">
        <div className={styles.features}>
          <div className={styles.featureCard}>
            <h3 className={styles.featureTitle}>Monthly Contributions</h3>
            <p className={styles.featureDesc}>
              Contribute USDC via Solana with transparent fee breakdowns and
              instant on-chain settlement tracking.
            </p>
          </div>
          <div className={styles.featureCard}>
            <h3 className={styles.featureTitle}>Fair Lending</h3>
            <p className={styles.featureDesc}>
              Request loans evaluated by membership history and pool health.
              Larger loans go through community governance votes.
            </p>
          </div>
          <div className={styles.featureCard}>
            <h3 className={styles.featureTitle}>Full Transparency</h3>
            <p className={styles.featureDesc}>
              Pool balances, loan performance, and aggregate metrics are public.
              Your personal details remain private.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}

import Link from "next/link";
import styles from "./page.module.css";

export default function OnboardingPage() {
  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Get started in 3 steps</h2>
      <p className={styles.sub}>
        Link your Telegram account and you can begin contributing right away.
      </p>

      <div className={styles.steps}>
        <div className={styles.step}>
          <span className={styles.stepNumber}>1</span>
          <div className={styles.stepContent}>
            <h3>Verify your email</h3>
            <p>
              Check your inbox for the verification link we sent during signup.
            </p>
          </div>
        </div>

        <div className={styles.step}>
          <span className={styles.stepNumber}>2</span>
          <div className={styles.stepContent}>
            <h3>Link Telegram</h3>
            <p>
              Open our Telegram bot and send <code>/start</code>. The bot will
              link your chat ID to your SACCO account automatically.
            </p>
          </div>
        </div>

        <div className={styles.step}>
          <span className={styles.stepNumber}>3</span>
          <div className={styles.stepContent}>
            <h3>Make your first contribution</h3>
            <p>
              Send <code>/contribute 20</code> in the bot to get a Transak
              payment link. Complete the payment to contribute USDC to the SACCO pool.
            </p>
          </div>
        </div>
      </div>

      <div className={styles.cta}>
        <Link href="/dashboard/member" className="btn btn-primary">
          Go to My Dashboard
        </Link>
      </div>
    </div>
  );
}

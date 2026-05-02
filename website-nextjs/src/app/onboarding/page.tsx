import Link from "next/link";
import styles from "./page.module.css";

const TELEGRAM_BOT_URL = "https://t.me/Lemaiyan_labs_bot";

export default function OnboardingPage() {
  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Get started in 3 steps</h2>
      <p className={styles.sub}>
        Verify your email, link Telegram with your phone number, and you can begin contributing right away.
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
              Open{" "}
              <a href={TELEGRAM_BOT_URL} target="_blank" rel="noopener noreferrer">
                @Lemaiyan_labs_bot
              </a>{" "}
              on Telegram, send <code>/start</code>, then tap <code>Share phone number</code>.
              The bot will match it with the phone number you used during signup.
            </p>
          </div>
        </div>

        <div className={styles.step}>
          <span className={styles.stepNumber}>3</span>
          <div className={styles.stepContent}>
            <h3>Make your first contribution</h3>
            <p>
              Send <code>/contribute 20</code> in the bot to get a payment link.
              Complete the payment to contribute USDC to the SACCO pool.
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

import Link from "next/link";
import styles from "./Nav.module.css";

export function Nav() {
  return (
    <nav className={styles.nav}>
      <Link href="/" className={styles.logo}>
        Blockchain<span className={styles.logoAccent}> SACCO</span>
      </Link>
      <ul className={styles.links}>
        <li>
          <Link href="/dashboard/public" className={styles.link}>
            Dashboard
          </Link>
        </li>
        <li>
          <Link href="/governance" className={styles.link}>
            Governance
          </Link>
        </li>
        <li>
          <Link href="/signup" className={`btn btn-primary ${styles.cta}`}>
            Sign Up
          </Link>
        </li>
      </ul>
    </nav>
  );
}

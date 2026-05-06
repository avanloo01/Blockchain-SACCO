"use client";

import { useState } from "react";
import Link from "next/link";
import styles from "./Nav.module.css";

export function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className={styles.nav}>
      <Link href="/" className={styles.logo}>
        Blockchain<span className={styles.logoAccent}> SACCO</span>
      </Link>
      <button
        className={styles.hamburger}
        aria-label="Toggle navigation"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span />
        <span />
        <span />
      </button>
      <ul className={`${styles.links} ${open ? styles.linksOpen : ""}`}>
        <li>
          <Link href="/dashboard/public" className={styles.link} onClick={() => setOpen(false)}>
            Dashboard
          </Link>
        </li>
        <li>
          <Link href="/governance" className={styles.link} onClick={() => setOpen(false)}>
            Governance
          </Link>
        </li>
        <li>
          <Link href="/signup" className={`btn btn-primary ${styles.cta}`} onClick={() => setOpen(false)}>
            Sign Up
          </Link>
        </li>
      </ul>
    </nav>
  );
}

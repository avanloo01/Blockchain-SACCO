"use client";

import { useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (res.ok) {
      setSubmitted(true);
    } else {
      const body = await res.json().catch(() => ({}));
      setError(
        (body as { error?: string }).error ||
          "Something went wrong. Please try again.",
      );
    }
  }

  if (submitted) {
    return (
      <div className={styles.page}>
        <h2 className={styles.title}>Check your email</h2>
        <p className={styles.sub}>
          If <strong>{email}</strong> is registered, we sent a sign-in link.
          Click it to access your account.
        </p>
        <p className={styles.hint}>
          The link expires in 15 minutes. Didn&apos;t receive it? Check your
          spam folder or{" "}
          <button
            className={styles.resend}
            onClick={() => setSubmitted(false)}
          >
            try again
          </button>
          .
        </p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Sign in</h2>
      <p className={styles.sub}>
        Enter your email and we&apos;ll send you a sign-in link.
      </p>

      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" className={`btn btn-primary ${styles.submit}`}>
          Send sign-in link
        </button>
      </form>

      <p className={styles.alt} style={{ marginTop: "1.5rem" }}>
        Don&apos;t have an account?{" "}
        <Link href="/signup">Sign up</Link>
      </p>
    </div>
  );
}

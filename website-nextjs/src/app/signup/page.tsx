"use client";

import { useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, phone, walletAddress: walletAddress || undefined }),
    });
    if (res.ok) {
      setSubmitted(true);
    }
  }

  if (submitted) {
    return (
      <div className={styles.page}>
        <h2 className={styles.title}>Check your email</h2>
        <p className={styles.sub}>
          We sent a verification link to <strong>{email}</strong>. Click it to
          activate your account, then continue to onboarding.
        </p>
        <Link href="/onboarding" className="btn btn-primary" style={{ width: "100%" }}>
          Continue to Onboarding
        </Link>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Create your account</h2>
      <p className={styles.sub}>
        Join the SACCO to start contributing and accessing loans.
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
        <div className={styles.field}>
          <label htmlFor="phone">Phone number</label>
          <input
            id="phone"
            type="tel"
            required
            autoComplete="tel"
            placeholder="+254 700 000000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </div>
        <div className={styles.field}>
          <label htmlFor="wallet">Wallet address (optional)</label>
          <input
            id="wallet"
            type="text"
            autoComplete="off"
            placeholder="0x... or Solana address"
            value={walletAddress}
            onChange={(e) => setWalletAddress(e.target.value)}
          />
          <p className={styles.hint}>
            Don&apos;t have a wallet?{" "}
            Try{" "}
            <a href="https://metamask.io" target="_blank" rel="noopener noreferrer">MetaMask</a>,{" "}
            <a href="https://trustwallet.com" target="_blank" rel="noopener noreferrer">Trust Wallet</a>, or{" "}
            <a href="https://phantom.app" target="_blank" rel="noopener noreferrer">Phantom</a>.
          </p>
        </div>
        <button type="submit" className={`btn btn-primary ${styles.submit}`}>
          Sign Up
        </button>
      </form>

      <p className={styles.alt} style={{ marginTop: "1.5rem" }}>
        Already have an account? <Link href="/api/auth/signin">Sign in</Link>
      </p>
    </div>
  );
}

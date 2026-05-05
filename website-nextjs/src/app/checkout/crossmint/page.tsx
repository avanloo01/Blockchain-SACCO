"use client";

import Link from "next/link";
import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  CrossmintCheckoutProvider,
  CrossmintEmbeddedCheckout,
  CrossmintProvider,
  useCrossmintCheckout,
} from "@crossmint/client-sdk-react-ui";

import styles from "./page.module.css";

function LoadingShell() {
  return (
    <div className={styles.shell}>
      <section className={styles.heroCard}>
        <p className={styles.eyebrow}>Crossmint Checkout</p>
        <h1>Loading secure contribution checkout</h1>
        <p className={styles.lead}>
          Preparing the payment session for your SACCO contribution.
        </p>
      </section>
    </div>
  );
}

function VerifyCommand({ intentId }: { intentId: string }) {
  const [copied, setCopied] = useState(false);
  const command = `/verify ${intentId}`;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className={styles.verifyBlock}>
      <span className={styles.label}>Telegram confirmation</span>
      <code className={styles.command}>{command}</code>
      <button type="button" className="btn btn-outline" onClick={handleCopy}>
        {copied ? "Copied" : "Copy command"}
      </button>
    </div>
  );
}

function StatusPanel({ intentId }: { intentId: string }) {
  const { order } = useCrossmintCheckout();
  const phase = typeof order?.phase === "string" ? order.phase : "waiting";
  const isComplete = phase === "completed";

  return (
    <aside className={styles.statusCard}>
      <div className={styles.statusHeader}>
        <span className={styles.label}>Checkout status</span>
        <span
          className={`${styles.phaseBadge} ${isComplete ? styles.phaseComplete : ""}`}
        >
          {phase}
        </span>
      </div>
      <p className={styles.statusText}>
        {isComplete
          ? "Payment completed. Return to Telegram and confirm the contribution so the SACCO ledger is updated."
          : "Complete the checkout, then return to Telegram and run the verification command below."}
      </p>
      <VerifyCommand intentId={intentId} />
      <div className={styles.helperLinks}>
        <Link href="/dashboard/member">Member dashboard</Link>
        <Link href="/onboarding">Onboarding guide</Link>
      </div>
    </aside>
  );
}

function InvalidLink({ reason }: { reason: string }) {
  return (
    <div className={styles.shell}>
      <section className={styles.heroCard}>
        <p className={styles.eyebrow}>Crossmint Checkout</p>
        <h1>Invalid checkout link</h1>
        <p className={styles.lead}>{reason}</p>
        <p className={styles.supportText}>
          Request a new contribution link from Telegram with <strong>/contribute</strong>.
        </p>
      </section>
    </div>
  );
}

function CrossmintCheckoutContent() {
  const searchParams = useSearchParams();
  const apiKey = process.env.NEXT_PUBLIC_CROSSMINT_CLIENT_API_KEY ?? "";

  const orderId = searchParams.get("orderId")?.trim() ?? "";
  const clientSecret = searchParams.get("clientSecret")?.trim() ?? "";
  const intentId = searchParams.get("intentId")?.trim() || orderId;
  const amount = searchParams.get("amount")?.trim() ?? "";

  const amountLabel = useMemo(() => {
    const parsed = Number(amount);
    return Number.isFinite(parsed) ? `${parsed.toFixed(2)} USD` : "Contribution checkout";
  }, [amount]);

  if (!apiKey) {
    return (
      <InvalidLink reason="The website is missing the API key." />
    );
  }

  if (!orderId) {
    return <InvalidLink reason="The payment link is missing the Crossmint order ID." />;
  }

  return (
    <div className={styles.shell}>
      <section className={styles.heroCard}>
        <div className={styles.heroCopy}>
          <p className={styles.eyebrow}>Crossmint Checkout</p>
          <h1>Complete your SACCO contribution</h1>
          <p className={styles.lead}>
            This secure checkout sends the purchased USDC to the SACCO Crossmint treasury wallet.
          </p>
        </div>
        <div className={styles.heroMeta}>
          <div>
            <span className={styles.label}>Intent ID</span>
            <strong>{intentId}</strong>
          </div>
          <div>
            <span className={styles.label}>Amount</span>
            <strong>{amountLabel}</strong>
          </div>
        </div>
      </section>

      <div className={styles.grid}>
        <section className={styles.checkoutCard}>
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.label}>Secure payment</span>
              <h2>Crossmint embedded checkout</h2>
            </div>
            <p className={styles.supportText}>
              Use card, Apple Pay, or Google Pay if available in your region.
            </p>
          </div>

          <CrossmintProvider apiKey={apiKey}>
            <CrossmintCheckoutProvider>
              <CrossmintEmbeddedCheckout
                orderId={orderId}
                clientSecret={clientSecret || undefined}
                payment={{
                  fiat: {
                    enabled: true,
                    allowedMethods: {
                      card: true,
                      applePay: true,
                      googlePay: true,
                    },
                  },
                  crypto: {
                    enabled: false,
                  },
                  defaultMethod: "fiat",
                }}
                appearance={{
                  variables: {
                    fontFamily: "var(--font-sans)",
                    borderRadius: "20px",
                    colors: {
                      backgroundPrimary: "#12151c",
                      borderPrimary: "#273244",
                      textPrimary: "#f5f7fb",
                      textSecondary: "#9fb0c7",
                      accent: "#2dd4bf",
                      warning: "#f59e0b",
                      danger: "#fb7185",
                    },
                  },
                  rules: {
                    DestinationInput: {
                      display: "hidden",
                    },
                  },
                }}
              />
              <StatusPanel intentId={intentId} />
            </CrossmintCheckoutProvider>
          </CrossmintProvider>
        </section>

        <aside className={styles.infoColumn}>
          <section className={styles.infoCard}>
            <span className={styles.label}>What happens next</span>
            <ol className={styles.steps}>
              <li>Finish the Crossmint checkout on this page.</li>
              <li>Return to Telegram after the payment succeeds.</li>
              <li>Run the copied verification command to finalize your contribution.</li>
            </ol>
          </section>

          <section className={styles.infoCard}>
            <span className={styles.label}>Notes</span>
            <p className={styles.supportText}>
              Members can keep using their own wallets elsewhere in the SACCO flow. This checkout settles into the SACCO treasury wallet, and Crossmint may still collect a receipt email for the payment method.
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}

export default function CrossmintCheckoutPage() {
  return (
    <Suspense fallback={<LoadingShell />}>
      <CrossmintCheckoutContent />
    </Suspense>
  );
}
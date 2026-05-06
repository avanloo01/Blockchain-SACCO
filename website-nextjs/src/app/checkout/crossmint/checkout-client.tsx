"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  CrossmintCheckoutProvider,
  CrossmintEmbeddedCheckout,
  CrossmintProvider,
  useCrossmintCheckout,
} from "@crossmint/client-sdk-react-ui";

import styles from "./page.module.css";

export function LoadingShell() {
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
  const orderId = typeof (order as Record<string, unknown> | undefined)?.orderId === "string"
    ? (order as Record<string, unknown>).orderId as string
    : null;
  const phase = typeof order?.phase === "string" ? order.phase : "waiting";
  const isComplete = phase === "completed";

  // As soon as Crossmint creates the order (client-side), link its orderId back
  // to our billing intent so the Telegram /verify command can look it up.
  const linkedRef = useRef(false);
  useEffect(() => {
    if (!orderId || !intentId || linkedRef.current) return;
    linkedRef.current = true;
    fetch("/api/checkout/link-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intentId, orderId }),
    }).catch(() => {
      linkedRef.current = false; // allow retry on next render
    });
  }, [orderId, intentId]);

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

interface CrossmintCheckoutContentProps {
  apiKey: string;
  tokenLocator: string;
  treasuryWallet: string;
}

export function CrossmintCheckoutContent({
  apiKey,
  tokenLocator,
  treasuryWallet,
}: CrossmintCheckoutContentProps) {
  const searchParams = useSearchParams();

  const intentId = searchParams.get("intentId")?.trim() ?? "";
  const amount = searchParams.get("amount")?.trim() ?? "";

  const amountLabel = useMemo(() => {
    const parsed = Number(amount);
    return Number.isFinite(parsed) ? `${parsed.toFixed(2)} USD` : "Contribution checkout";
  }, [amount]);

  if (!apiKey) {
    return <InvalidLink reason="The website is missing the API key." />;
  }

  if (!intentId) {
    return <InvalidLink reason="The payment link is missing the intent ID." />;
  }

  if (!tokenLocator || !treasuryWallet) {
    return <InvalidLink reason="The checkout is not yet configured. Please contact the SACCO admin." />;
  }

  const parsedAmount = Number(amount);
  if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
    return <InvalidLink reason="The payment link has an invalid amount." />;
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
          <div className={styles.metaItem}>
            <span className={styles.label}>Intent ID</span>
            <strong className={styles.metaValue}>{intentId}</strong>
          </div>
          <div className={styles.metaItem}>
            <span className={styles.label}>Amount</span>
            <strong className={styles.metaValue}>{amountLabel}</strong>
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
              Pay with card, Apple Pay, or connect a crypto wallet.
            </p>
          </div>

          <CrossmintProvider apiKey={apiKey}>
            <CrossmintCheckoutProvider>
              <div className={styles.embedShell}>
                <CrossmintEmbeddedCheckout
                  lineItems={{
                    tokenLocator,
                    executionParameters: {
                      mode: "exact-in",
                      amount: parsedAmount.toFixed(2),
                    },
                  }}
                  recipient={{ walletAddress: treasuryWallet }}
                  payment={{
                    fiat: {
                      enabled: true,
                      allowedMethods: {
                        card: true,
                        applePay: true,
                        googlePay: false,
                      },
                    },
                    crypto: {
                      enabled: true,
                    },
                    defaultMethod: "fiat",
                  }}
                  appearance={{
                    variables: {
                      fontFamily: "var(--font-sans)",
                      borderRadius: "18px",
                      colors: {
                        backgroundPrimary: "#0a111d",
                        borderPrimary: "#2f3f57",
                        textPrimary: "#2f3f57",
                        textSecondary: "#a2b4cc",
                        accent: "#2dd4bf",
                        warning: "#f59e0b",
                        danger: "#fb7185",
                      },
                    },
                    rules: {
                      DestinationInput: {
                        display: "hidden",
                      },
                      Label: {
                        colors: {
                          text: "#425066",
                        },
                      },
                      Input: {
                        borderRadius: "16px",
                        colors: {
                          text: "#0f1726",
                          background: "#ffffff",
                          border: "#8fa3c3",
                          boxShadow: "none",
                          placeholder: "#5f6f86",
                        },
                        focus: {
                          colors: {
                            background: "#ffffff",
                            border: "#2dd4bf",
                            boxShadow: "0 0 0 2px rgba(45, 212, 191, 0.35)",
                          },
                        },
                        hover: {
                          colors: {
                            background: "#f8fbff",
                            border: "#6f86a8",
                            boxShadow: "none",
                          },
                        },
                      },
                      Tab: {
                        borderRadius: "16px",
                        colors: {
                          text: "#1a2436",
                          background: "#eef3fa",
                          border: "#90a3bf",
                          boxShadow: "none",
                        },
                        selected: {
                          colors: {
                            text: "#0a1322",
                            background: "#dff8f4",
                            border: "#2dd4bf",
                            boxShadow: "0 0 0 2px rgba(45, 212, 191, 0.28)",
                          },
                        },
                        hover: {
                          colors: {
                            text: "#0f1a2d",
                            background: "#e6edf7",
                            border: "#6f86a8",
                            boxShadow: "none",
                          },
                        },
                      },
                      PrimaryButton: {
                        borderRadius: "14px",
                        colors: {
                          text: "#052230",
                          background: "#2dd4bf",
                        },
                        hover: {
                          colors: {
                            text: "#052230",
                            background: "#4fe3d1",
                          },
                        },
                      },
                    },
                  }}
                />
              </div>
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

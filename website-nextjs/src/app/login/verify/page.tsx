"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";

export default function LoginVerifyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"verifying" | "error">("verifying");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    const email = searchParams.get("email");

    if (!token || !email) {
      setErrorMessage("Invalid or missing login link.");
      setStatus("error");
      return;
    }

    signIn("magic-link", {
      email,
      loginToken: token,
      redirect: false,
    }).then((result) => {
      if (result?.ok) {
        router.replace("/dashboard/member");
      } else {
        setErrorMessage(
          "This sign-in link is invalid or has expired. Please request a new one.",
        );
        setStatus("error");
      }
    });
  }, [router, searchParams]);

  if (status === "error") {
    return (
      <div style={{ maxWidth: 440, margin: "4rem auto", padding: "0 1.25rem" }}>
        <h2>Sign-in failed</h2>
        <p style={{ color: "var(--foreground-muted)", marginBottom: "1.5rem" }}>
          {errorMessage}
        </p>
        <a href="/login" className="btn btn-primary">
          Back to sign-in
        </a>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 440, margin: "4rem auto", padding: "0 1.25rem" }}>
      <p style={{ color: "var(--foreground-muted)" }}>Signing you in…</p>
    </div>
  );
}

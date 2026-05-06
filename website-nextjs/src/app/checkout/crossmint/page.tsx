import { Suspense } from "react";
import { LoadingShell, CrossmintCheckoutContent } from "./checkout-client";

/**
 * Server component: reads Crossmint configuration from the runtime environment
 * and passes it as props to the client-side checkout form.
 *
 * Reading config here (server-side) instead of inside the client component
 * prevents empty values caused by env vars that were unset at build time from
 * being baked into the JS bundle. Server components always read from the live
 * runtime environment on every request.
 */
export default function CrossmintCheckoutPage() {
  const apiKey = process.env.NEXT_PUBLIC_CROSSMINT_CLIENT_API_KEY ?? "";
  const tokenLocator = process.env.NEXT_PUBLIC_CROSSMINT_TOKEN_LOCATOR ?? "";
  const treasuryWallet = process.env.NEXT_PUBLIC_CROSSMINT_WALLET_ADDRESS ?? "";

  return (
    <Suspense fallback={<LoadingShell />}>
      <CrossmintCheckoutContent
        apiKey={apiKey}
        tokenLocator={tokenLocator}
        treasuryWallet={treasuryWallet}
      />
    </Suspense>
  );
}


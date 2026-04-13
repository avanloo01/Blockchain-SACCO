import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

const FROM_ADDRESS =
  process.env.RESEND_FROM_EMAIL || "Blockchain SACCO <noreply@lemaiyanlabs.org>";

export async function sendVerificationEmail(
  to: string,
  verifyUrl: string,
): Promise<{ success: boolean; error?: string }> {
  const { error } = await resend.emails.send({
    from: FROM_ADDRESS,
    to,
    subject: "Verify your Blockchain SACCO account",
    html: `
      <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>Welcome to Blockchain SACCO</h2>
        <p>Click the button below to verify your email address and activate your account.</p>
        <a href="${verifyUrl}"
           style="display: inline-block; padding: 12px 24px; background: #2563eb;
                  color: #fff; text-decoration: none; border-radius: 6px; margin: 16px 0;">
          Verify Email
        </a>
        <p style="color: #666; font-size: 13px;">
          If the button doesn't work, copy and paste this link into your browser:<br/>
          <a href="${verifyUrl}">${verifyUrl}</a>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 24px;">
          If you did not sign up, you can safely ignore this email.
        </p>
      </div>
    `,
  });

  if (error) {
    return { success: false, error: error.message };
  }
  return { success: true };
}

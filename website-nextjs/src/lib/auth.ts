import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { createHash } from "crypto";
import { supabaseQuery, supabaseUpdate } from "@/lib/supabase";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id: "magic-link",
      name: "Magic Link",
      credentials: {
        email: { label: "Email", type: "email" },
        loginToken: { label: "Login Token", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.loginToken) return null;

        const hashed = createHash("sha256")
          .update(credentials.loginToken)
          .digest("hex");

        const { data: members } = await supabaseQuery<
          {
            id: string;
            email: string;
            login_token: string | null;
            login_token_expires_at: string | null;
          }[]
        >("members", {
          select: "id,email,login_token,login_token_expires_at",
          email: `eq.${credentials.email}`,
          login_token: `eq.${hashed}`,
          limit: "1",
        });

        if (!members || members.length === 0) return null;

        const member = members[0];

        if (
          member.login_token_expires_at &&
          new Date(member.login_token_expires_at) < new Date()
        ) {
          return null;
        }

        // Consume the token so it cannot be reused.
        await supabaseUpdate(
          "members",
          { id: `eq.${member.id}` },
          { login_token: null, login_token_expires_at: null },
        );

        return { id: member.id, email: member.email };
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.memberId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as Record<string, unknown>).memberId = token.memberId;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};

import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        // For MVP, accept any registered email.
        // In production, verify against Supabase Auth or a password hash.
        if (!credentials?.email) return null;
        return {
          id: credentials.email,
          email: credentials.email,
        };
      },
    }),
  ],
  pages: {
    signIn: "/signup",
  },
  session: {
    strategy: "jwt",
  },
  secret: process.env.NEXTAUTH_SECRET,
};

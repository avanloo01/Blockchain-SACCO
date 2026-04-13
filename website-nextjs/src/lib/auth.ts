import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { supabaseQuery } from "@/lib/supabase";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email) return null;

        const { data: members } = await supabaseQuery<
          { id: string; email: string }[]
        >("members", {
          select: "id,email",
          email: `eq.${credentials.email}`,
          limit: "1",
        });

        if (!members || members.length === 0) return null;

        return {
          id: members[0].id,
          email: members[0].email,
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

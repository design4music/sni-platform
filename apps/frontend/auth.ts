import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';
import LinkedIn from 'next-auth/providers/linkedin';
import bcrypt from 'bcryptjs';
import { query } from '@/lib/db';

import type { Provider } from 'next-auth/providers';

const providers: Provider[] = [];
if (process.env.AUTH_GOOGLE_ID) {
  providers.push(Google({ clientId: process.env.AUTH_GOOGLE_ID, clientSecret: process.env.AUTH_GOOGLE_SECRET! }));
}
if (process.env.AUTH_LINKEDIN_ID) {
  providers.push(LinkedIn({ clientId: process.env.AUTH_LINKEDIN_ID, clientSecret: process.env.AUTH_LINKEDIN_SECRET! }));
}
providers.push(Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const email = credentials?.email as string | undefined;
        const password = credentials?.password as string | undefined;
        if (!email || !password) return null;

        const rows = await query<{ id: string; email: string; name: string | null; password: string }>(
          'SELECT id, email, name, password FROM users WHERE email = $1',
          [email]
        );
        if (rows.length === 0) return null;

        const user = rows[0];
        const valid = await bcrypt.compare(password, user.password);
        if (!valid) return null;

        return { id: user.id, email: user.email, name: user.name };
      },
    }),
  );

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  providers,
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/auth/signin',
  },
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider && account.provider !== 'credentials') {
        const email = user.email?.toLowerCase().trim();
        if (!email) return false;

        // Check if user exists by email (account linking)
        const existing = await query<{ id: string }>(
          'SELECT id FROM users WHERE email = $1',
          [email]
        );

        if (existing.length > 0) {
          // Update provider info + avatar
          await query(
            `UPDATE users SET auth_provider = $1, provider_id = $2, avatar_url = COALESCE($3, avatar_url)
             WHERE id = $4`,
            [account.provider, account.providerAccountId, user.image || null, existing[0].id]
          );
          user.id = existing[0].id;
        } else {
          // Create new user (no password for social login)
          const rows = await query<{ id: string }>(
            `INSERT INTO users (email, name, avatar_url, auth_provider, provider_id, password)
             VALUES ($1, $2, $3, $4, $5, '')
             RETURNING id`,
            [email, user.name || null, user.image || null, account.provider, account.providerAccountId]
          );
          user.id = rows[0].id;
        }
      }
      return true;
    },
    async jwt({ token, user, trigger }) {
      if (user?.id) token.id = user.id;
      // Enrich token with role + focus_centroid on sign-in or update
      if (user?.id || trigger === 'update') {
        const id = (user?.id || token.id) as string;
        if (id) {
          const rows = await query<{ role: string; focus_centroid: string | null; avatar_url: string | null }>(
            'SELECT role, focus_centroid, avatar_url FROM users WHERE id = $1',
            [id]
          );
          if (rows.length > 0) {
            token.role = rows[0].role;
            token.focusCentroid = rows[0].focus_centroid;
            token.avatarUrl = rows[0].avatar_url;
          }
        }
      }
      return token;
    },
    session({ session, token }) {
      if (token.id) session.user.id = token.id as string;
      (session.user as any).role = token.role || 'user';
      (session.user as any).focusCentroid = token.focusCentroid || null;
      (session.user as any).avatarUrl = token.avatarUrl || null;
      return session;
    },
  },
});

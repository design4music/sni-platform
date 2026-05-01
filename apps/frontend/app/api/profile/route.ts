import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';
import { query } from '@/lib/db';

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  const rows = await query<{
    id: string;
    email: string;
    name: string | null;
    avatar_url: string | null;
    auth_provider: string;
    role: string;
    created_at: string;
  }>(
    `SELECT id, email, name, avatar_url, auth_provider, role, created_at
     FROM users WHERE id = $1`,
    [session.user.id]
  );

  if (rows.length === 0) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  return NextResponse.json(rows[0]);
}

export async function PATCH(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  const body = await req.json();
  const updates: string[] = [];
  const params: unknown[] = [];
  let paramIdx = 1;

  if ('name' in body && typeof body.name === 'string') {
    updates.push(`name = $${paramIdx++}`);
    params.push(body.name.trim() || null);
  }

  if (updates.length === 0) {
    return NextResponse.json({ error: 'No valid fields to update' }, { status: 400 });
  }

  params.push(session.user.id);
  await query(
    `UPDATE users SET ${updates.join(', ')}, updated_at = NOW() WHERE id = $${paramIdx}`,
    params as any[]
  );

  return NextResponse.json({ ok: true });
}

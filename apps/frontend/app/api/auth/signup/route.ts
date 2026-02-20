import { NextRequest, NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import { query } from '@/lib/db';

export async function POST(req: NextRequest) {
  let body: { email?: string; password?: string; name?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const { email, password, name } = body;

  if (!email || !password) {
    return NextResponse.json({ error: 'Email and password are required' }, { status: 400 });
  }

  if (password.length < 8) {
    return NextResponse.json({ error: 'Password must be at least 8 characters' }, { status: 400 });
  }

  const hash = await bcrypt.hash(password, 10);

  try {
    await query(
      'INSERT INTO users (email, name, password) VALUES ($1, $2, $3)',
      [email.toLowerCase().trim(), name?.trim() || null, hash]
    );
  } catch (err: any) {
    if (err.code === '23505') {
      return NextResponse.json({ error: 'An account with this email already exists' }, { status: 409 });
    }
    throw err;
  }

  return NextResponse.json({ ok: true }, { status: 201 });
}

import { NextRequest, NextResponse } from 'next/server';
import { getTopSignalsAll } from '@/lib/queries';

export async function GET(req: NextRequest) {
  try {
    const sp = req.nextUrl.searchParams;
    const perType = Math.min(parseInt(sp.get('perType') || '8', 10), 20);
    const month = sp.get('month') || undefined;
    const nodes = await getTopSignalsAll(perType, month);
    return NextResponse.json(nodes);
  } catch (err: unknown) {
    console.error('signals/top error:', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { getSignalGraph } from '@/lib/queries';

export async function GET(req: NextRequest) {
  try {
    const sp = req.nextUrl.searchParams;
    const perType = Math.min(parseInt(sp.get('perType') || '8', 10), 20);
    const month = sp.get('month') || undefined;
    const graph = await getSignalGraph(perType, month);
    return NextResponse.json(graph);
  } catch (err: unknown) {
    console.error('signals/co-occurrence error:', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

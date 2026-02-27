import { NextRequest, NextResponse } from 'next/server';
import { getSignalCategoryDetail } from '@/lib/queries';
import { SignalType } from '@/lib/types';

const VALID_TYPES = new Set<string>([
  'persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events',
]);

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ type: string }> },
) {
  try {
    const { type } = await params;
    if (!VALID_TYPES.has(type)) {
      return NextResponse.json({ error: 'Invalid signal type' }, { status: 400 });
    }
    const sp = req.nextUrl.searchParams;
    const limit = Math.min(parseInt(sp.get('limit') || '10', 10), 30);
    const month = sp.get('month') || undefined;
    const entries = await getSignalCategoryDetail(type as SignalType, limit, month);
    return NextResponse.json(entries);
  } catch (err: unknown) {
    console.error('signals/[type] error:', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

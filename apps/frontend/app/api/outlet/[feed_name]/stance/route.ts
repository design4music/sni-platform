import { NextRequest, NextResponse } from 'next/server';
import { getOutletStance } from '@/lib/queries';

// Editorial stance matrix for an outlet, month-scoped.
// Client calls this from OutletStanceSection on month switch.
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ feed_name: string }> }
) {
  const { feed_name } = await params;
  const month = req.nextUrl.searchParams.get('month');
  if (!month || !/^\d{4}-\d{2}$/.test(month)) {
    return NextResponse.json({ error: 'Missing or malformed month' }, { status: 400 });
  }
  const entities = await getOutletStance(decodeURIComponent(feed_name), month);
  return NextResponse.json({ entities });
}

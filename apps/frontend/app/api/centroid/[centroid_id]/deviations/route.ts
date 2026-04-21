import { NextRequest, NextResponse } from 'next/server';
import { getCentroidDeviationsForMonth } from '@/lib/queries';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ centroid_id: string }> }
) {
  const { centroid_id } = await params;
  const month = request.nextUrl.searchParams.get('month');
  if (!month || !/^\d{4}-\d{2}$/.test(month)) {
    return NextResponse.json({ error: 'month must be YYYY-MM' }, { status: 400 });
  }
  try {
    const weeks = await getCentroidDeviationsForMonth(centroid_id, month);
    return NextResponse.json({ weeks });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'unknown error';
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

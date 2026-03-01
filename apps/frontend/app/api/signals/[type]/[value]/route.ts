import { NextRequest, NextResponse } from 'next/server';
import { getSignalStats, getRelationshipClusters } from '@/lib/queries';
import { SignalType } from '@/lib/types';

const VALID_TYPES = new Set<string>([
  'persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events',
]);

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ type: string; value: string }> },
) {
  try {
    const { type, value } = await params;
    if (!VALID_TYPES.has(type)) {
      return NextResponse.json({ error: 'Invalid signal type' }, { status: 400 });
    }
    const decoded = decodeURIComponent(value);
    const month = req.nextUrl.searchParams.get('month') || undefined;
    const [stats, clusters] = await Promise.all([
      getSignalStats(type as SignalType, decoded, month),
      getRelationshipClusters(type as SignalType, decoded, month),
    ]);
    return NextResponse.json({
      signal_type: type,
      value: decoded,
      total_events: stats.total,
      weekly: stats.weekly,
      geo: stats.geo,
      tracks: stats.tracks,
      relationship_clusters: clusters,
    });
  } catch (err: unknown) {
    console.error('signals/[type]/[value] error:', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

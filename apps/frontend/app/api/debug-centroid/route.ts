import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const results: Record<string, any> = {};
  const centroidId = 'AMERICAS-USA';
  const month = '2026-03';

  // Test 1: getCentroidById
  try {
    const r = await query(
      'SELECT id, label FROM centroids_v3 WHERE id = $1 AND is_active = true',
      [centroidId]
    );
    results.getCentroidById = { ok: true, rows: r.length };
  } catch (e: any) {
    results.getCentroidById = { ok: false, error: e.message };
  }

  // Test 2: getAvailableMonthsForCentroid
  try {
    const r = await query(
      "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month FROM ctm WHERE centroid_id = $1 ORDER BY month DESC",
      [centroidId]
    );
    results.getAvailableMonths = { ok: true, rows: r.length, data: r.slice(0, 3) };
  } catch (e: any) {
    results.getAvailableMonths = { ok: false, error: e.message };
  }

  // Test 3: getConfiguredTracksForCentroid
  try {
    const r = await query(
      'SELECT tc.tracks FROM centroids_v3 c JOIN track_configs tc ON c.track_config_id = tc.id WHERE c.id = $1',
      [centroidId]
    );
    results.getConfiguredTracks = { ok: true, rows: r.length };
  } catch (e: any) {
    results.getConfiguredTracks = { ok: false, error: e.message };
  }

  // Test 4: getTrackSummaryByCentroidAndMonth (SARGable)
  try {
    const r = await query(
      `SELECT c.track, COUNT(DISTINCT ta.title_id)::int as title_count, MAX(e.last_active)::text as last_active
       FROM ctm c
       LEFT JOIN title_assignments ta ON c.id = ta.ctm_id
       LEFT JOIN events_v3 e ON e.ctm_id = c.id
       WHERE c.centroid_id = $1 AND c.month = ($2 || '-01')::date
       GROUP BY c.track ORDER BY c.track`,
      [centroidId, month]
    );
    results.getTrackSummary = { ok: true, rows: r.length };
  } catch (e: any) {
    results.getTrackSummary = { ok: false, error: e.message };
  }

  // Test 5: getCentroidMonthlySummary (SARGable)
  try {
    const r = await query(
      `SELECT summary_text, track_count, total_events
       FROM centroid_monthly_summaries
       WHERE centroid_id = $1 AND month = ($2 || '-01')::date`,
      [centroidId, month]
    );
    results.getCentroidMonthlySummary = { ok: true, rows: r.length };
  } catch (e: any) {
    results.getCentroidMonthlySummary = { ok: false, error: e.message };
  }

  // Test 6: getTopSignalsForCentroid (mv_centroid_signals)
  try {
    const r = await query(
      `SELECT signals FROM mv_centroid_signals
       WHERE centroid_id = $1 AND month = ($2 || '-01')::date`,
      [centroidId, month]
    );
    results.getTopSignals = { ok: true, rows: r.length, hasData: r.length > 0 };
  } catch (e: any) {
    results.getTopSignals = { ok: false, error: e.message };
  }

  // Test 7: Check table existence
  try {
    const r = await query(
      `SELECT table_name FROM information_schema.tables
       WHERE table_schema = 'public' AND table_name IN ('mv_centroid_signals', 'mv_signal_graph', 'centroid_top_signals')
       ORDER BY table_name`
    );
    results.tables = { ok: true, found: r.map((x: any) => x.table_name) };
  } catch (e: any) {
    results.tables = { ok: false, error: e.message };
  }

  return NextResponse.json(results, { status: 200 });
}

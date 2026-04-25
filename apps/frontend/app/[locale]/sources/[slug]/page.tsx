/**
 * /sources/[slug]
 *
 * Outlet entry point. Redirects (302) to the most recent month with
 * outlet_entity_stance data, or — if the outlet has no stance rows yet —
 * to the most recent month for which we have publisher_stats_monthly. If
 * neither exists (very new or very small outlets), redirects to the
 * /sources index.
 *
 * The redirect lives here so that bare /sources/[slug] URLs are still
 * valid (back-compat with old links and search-index entries) but the
 * canonical, indexable URL is /sources/[slug]/[YYYY-MM]. The redirect
 * is intentionally 307/302 (temporary), not 301: the target month
 * shifts forward each month as new data lands.
 */

import { redirect, notFound } from 'next/navigation';
import { resolveSlug } from '@/lib/slug-server';
import { generateSlug } from '@/lib/slug';
import { query } from '@/lib/db';

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

export const dynamic = 'force-dynamic';

export default async function OutletEntryPage({ params }: Props) {
  const { locale, slug } = await params;
  const decoded = decodeURIComponent(slug);

  // First try the slug as-is (lowercased). If it doesn't match, treat the
  // input as a possibly-legacy outlet name (URL-encoded, spaces, mixed
  // case) and slugify it — covers /sources/Der%20Spiegel → der-spiegel.
  let canonicalSlug = decoded.toLowerCase();
  let feedName = await resolveSlug(canonicalSlug);
  if (!feedName) {
    canonicalSlug = generateSlug(decoded);
    feedName = await resolveSlug(canonicalSlug);
    if (feedName && canonicalSlug !== decoded.toLowerCase()) {
      // Permanent redirect from the legacy URL form to the canonical slug URL.
      redirect(`/${locale}/sources/${canonicalSlug}`);
    }
  }
  if (!feedName) notFound();

  // Pick the most recent month with stance rows; fall back to the most
  // recent month with monthly publisher stats; both queries are cheap
  // index lookups.
  const stanceMonth = await query<{ m: string }>(
    `SELECT TO_CHAR(month, 'YYYY-MM') AS m
     FROM outlet_entity_stance
     WHERE outlet_name = $1
     ORDER BY month DESC LIMIT 1`,
    [feedName]
  );
  const statsMonth = stanceMonth[0]?.m
    ? null
    : await query<{ m: string }>(
        `SELECT TO_CHAR(month, 'YYYY-MM') AS m
         FROM mv_publisher_stats_monthly
         WHERE feed_name = $1
         ORDER BY month DESC LIMIT 1`,
        [feedName]
      );

  const target = stanceMonth[0]?.m || statsMonth?.[0]?.m;
  if (!target) {
    // Nothing to show; bounce to the sources index.
    redirect(`/${locale}/sources`);
  }
  redirect(`/${locale}/sources/${canonicalSlug}/${target}`);
}

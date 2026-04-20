import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getStanceMatrix } from '@/lib/queries';
import { buildAlternates } from '@/lib/seo';
import { getTranslations } from 'next-intl/server';
import { getCentroidLabel } from '@/lib/types';
import { getOutletLogoUrl } from '@/lib/logos';
import Link from 'next/link';
import AlignmentHeatmap from './AlignmentHeatmap';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: 'Media Alignment',
    description: 'How major publishers cover different countries and regions.',
    alternates: buildAlternates('/sources/alignment'),
  };
}

export default async function AlignmentPage() {
  const t = await getTranslations('sources');
  const tCentroids = await getTranslations('centroids');
  const rows = await getStanceMatrix();

  // Build matrix data: publishers (rows) x centroids (columns)
  const publisherMap = new Map<string, { domain: string | null; country: string | null; scores: Record<string, number> }>();
  const centroidSet = new Map<string, string>(); // id -> label

  for (const r of rows) {
    if (!publisherMap.has(r.feed_name)) {
      publisherMap.set(r.feed_name, { domain: r.source_domain, country: r.country_code, scores: {} });
    }
    publisherMap.get(r.feed_name)!.scores[r.centroid_id] = r.score;
    if (!centroidSet.has(r.centroid_id)) {
      centroidSet.set(r.centroid_id, getCentroidLabel(r.centroid_id, r.centroid_label, tCentroids));
    }
  }

  // Sort centroids by how many publishers cover them (most covered first)
  const centroidCoverage = new Map<string, number>();
  for (const [, pub] of publisherMap) {
    for (const cid of Object.keys(pub.scores)) {
      centroidCoverage.set(cid, (centroidCoverage.get(cid) || 0) + 1);
    }
  }
  const centroids = [...centroidSet.entries()]
    .sort((a, b) => (centroidCoverage.get(b[0]) || 0) - (centroidCoverage.get(a[0]) || 0));

  // Sort publishers by coverage breadth, then alphabetically
  const publishers = [...publisherMap.entries()]
    .sort((a, b) => {
      const diff = Object.keys(b[1].scores).length - Object.keys(a[1].scores).length;
      return diff !== 0 ? diff : a[0].localeCompare(b[0]);
    })
    .map(([name, data]) => ({
      name,
      domain: data.domain,
      country: data.country,
      logoUrl: data.domain ? getOutletLogoUrl(data.domain, 16) : '',
      scores: data.scores,
    }));

  return (
    <DashboardLayout>
      <div className="max-w-[1400px] mx-auto">
        <div className="mb-6">
          <Link href="/sources" className="text-blue-400 hover:text-blue-300 text-sm">
            &larr; {t('allSources')}
          </Link>
          <h1 className="text-3xl font-bold mt-3">{t('alignmentTitle')}</h1>
          <p className="text-dashboard-text-muted mt-1">{t('alignmentDesc')}</p>
        </div>

        <AlignmentHeatmap
          publishers={publishers}
          centroids={centroids}
        />
      </div>
    </DashboardLayout>
  );
}

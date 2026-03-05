import Link from 'next/link';
import { Centroid, getCentroidLabel } from '@/lib/types';
import { getTranslations } from 'next-intl/server';

interface CentroidCardProps {
  centroid: Centroid;
  showClass?: boolean;
}

export default async function CentroidCard({ centroid, showClass = false }: CentroidCardProps) {
  const t = await getTranslations('centroidCard');
  const tTrending = await getTranslations('trending');
  const tCentroids = await getTranslations('centroids');
  const sourceCount = centroid.source_count || 0;
  const monthCount = centroid.month_source_count || 0;
  const hasArticles = sourceCount > 0;
  const isFresh = !!(centroid.last_article_date &&
    (Date.now() - new Date(centroid.last_article_date).getTime()) < 172800000);

  return (
    <Link
      href={`/c/${centroid.id}`}
      className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-lg font-semibold flex-1">{getCentroidLabel(centroid.id, centroid.label, tCentroids)}</h3>
            {isFresh && (
              <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" title={tTrending('active48h')} />
            )}
          </div>
          {centroid.description && (
            <p className="text-sm text-dashboard-text-muted mb-2">{centroid.description}</p>
          )}
          {hasArticles && (
            <div className="flex flex-wrap gap-3 text-xs text-dashboard-text-muted mt-2">
              <span>{monthCount.toLocaleString()} {t('thisMonth')}</span>
              <span className="opacity-50">|</span>
              <span>{sourceCount.toLocaleString()} {t('allTime')}</span>
            </div>
          )}
          {showClass && (
            <span className="text-xs px-2 py-1 rounded bg-dashboard-border text-dashboard-text-muted inline-block mt-2">
              {centroid.class === 'geo' ? t('geographic') : t('systemic')}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

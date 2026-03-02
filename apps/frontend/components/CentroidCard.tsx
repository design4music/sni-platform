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
  const tCommon = await getTranslations('common');
  const tCentroids = await getTranslations('centroids');
  const articleCount = centroid.article_count || 0;
  const hasArticles = articleCount > 0;
  const sourceCount = centroid.source_count || 0;
  const languageCount = centroid.language_count || 0;
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
            {centroid.article_count !== undefined && (
              <span
                className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium ${
                  hasArticles
                    ? 'bg-green-500/10 border-green-500/30 text-green-400'
                    : 'bg-red-500/10 border-red-500/30 text-red-400'
                }`}
                title={hasArticles ? `${articleCount.toLocaleString()} ${t('totalArticles')}` : t('noArticles')}
              >
                {hasArticles ? (
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                <span className="tabular-nums">{articleCount.toLocaleString()}</span>
                {isFresh && (
                  <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" title={tTrending('active48h')} />
                )}
              </span>
            )}
          </div>
          {centroid.description && (
            <p className="text-sm text-dashboard-text-muted mb-2">{centroid.description}</p>
          )}
          {hasArticles && (sourceCount > 0 || languageCount > 0) && (
            <div className="flex flex-wrap gap-3 text-xs text-dashboard-text-muted mt-2">
              {sourceCount > 0 && (
                <span title={`${sourceCount} ${t('distinctSources')}`}>
                  {sourceCount} {tCommon('sources')}
                </span>
              )}
              {languageCount > 0 && (
                <span title={`${t('coverageIn')} ${languageCount} ${t('languages')}`}>
                  {languageCount} {languageCount === 1 ? t('language') : t('languages')}
                </span>
              )}
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

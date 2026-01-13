import Link from 'next/link';
import { Centroid } from '@/lib/types';

interface CentroidCardProps {
  centroid: Centroid;
  showClass?: boolean;
}

export default function CentroidCard({ centroid, showClass = false }: CentroidCardProps) {
  const articleCount = centroid.article_count || 0;
  const hasArticles = articleCount > 0;

  return (
    <Link
      href={`/c/${centroid.id}`}
      className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-lg font-semibold">{centroid.label}</h3>
            {centroid.article_count !== undefined && (
              <span
                className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium ${
                  hasArticles
                    ? 'bg-green-500/10 border-green-500/30 text-green-400'
                    : 'bg-red-500/10 border-red-500/30 text-red-400'
                }`}
                title={hasArticles ? `${articleCount.toLocaleString()} total articles` : 'No articles yet'}
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
              </span>
            )}
          </div>
          {centroid.description && (
            <p className="text-sm text-dashboard-text-muted">{centroid.description}</p>
          )}
          {showClass && (
            <span className="text-xs px-2 py-1 rounded bg-dashboard-border text-dashboard-text-muted inline-block mt-2">
              {centroid.class === 'geo' ? 'Geographic' : 'Systemic'}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

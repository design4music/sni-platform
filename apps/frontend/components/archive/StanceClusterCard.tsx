'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { useLocale, useTranslations } from 'next-intl';

interface ClusterInfo {
  label: string;
  cluster_label: string;
  cluster_publishers: string[];
  cluster_score_avg: number;
  title_count: number;
  description: string | null;
}

interface Props {
  clusters: ClusterInfo[];
  entityType: string;
  entityId: string;
  synthesis?: string | null;
  blindSpots?: string[] | null;
  frameDivergence?: number | null;
  hasFullReport?: boolean;
}

const CLUSTER_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  critical: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    dot: 'bg-red-500',
  },
  reportorial: {
    bg: 'bg-slate-500/10',
    border: 'border-slate-500/30',
    text: 'text-slate-400',
    dot: 'bg-slate-400',
  },
  supportive: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    dot: 'bg-green-500',
  },
};

function DivergenceBadge({ value, t }: { value: number; t: (key: string) => string }) {
  const level = value >= 0.7 ? t('highDivergence') : value >= 0.4 ? t('mediumDivergence') : t('lowDivergence');
  const cls = value >= 0.7
    ? 'bg-red-500/20 text-red-400 border-red-500/30'
    : value >= 0.4
      ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      : 'bg-green-500/20 text-green-400 border-green-500/30';
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${cls}`}>
      {level}
    </span>
  );
}

export default function StanceClusterCard({
  clusters,
  entityType,
  entityId,
  synthesis,
  blindSpots,
  frameDivergence,
  hasFullReport,
}: Props) {
  const { data: session } = useSession();
  const locale = useLocale();
  const t = useTranslations('stanceCluster');
  const prefix = locale === 'de' ? '/de' : '';

  const totalTitles = clusters.reduce((sum, c) => sum + c.title_count, 0);

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-dashboard-text">{t('title')}</h3>
        {frameDivergence != null && <DivergenceBadge value={frameDivergence} t={t} />}
      </div>

      <p className="text-xs text-dashboard-text-muted">
        {t('clusterCount', { count: clusters.length, titles: totalTitles })}
      </p>

      {/* Cluster cards */}
      <div className="space-y-2">
        {clusters.map((c, i) => {
          const colors = CLUSTER_COLORS[c.cluster_label] || CLUSTER_COLORS.reportorial;
          const topPubs = c.cluster_publishers.slice(0, 3);
          const extra = c.cluster_publishers.length - 3;
          return (
            <div
              key={`${c.cluster_label}-${i}`}
              className={`p-2.5 rounded-lg border ${colors.bg} ${colors.border}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full ${colors.dot}`} />
                <span className={`text-xs font-semibold uppercase tracking-wide ${colors.text}`}>
                  {c.cluster_label}
                </span>
                <span className="text-xs text-dashboard-text-muted ml-auto">
                  {t('publishers', { count: c.cluster_publishers.length })}
                </span>
              </div>
              <p className="text-sm font-medium text-dashboard-text mb-1">{c.label}</p>
              <p className="text-xs text-dashboard-text-muted">
                {topPubs.join(', ')}{extra > 0 ? ` ${t('morePublishers', { count: extra })}` : ''}
              </p>
            </div>
          );
        })}
      </div>

      {/* Synthesis */}
      {synthesis && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            {t('summary')}
          </h4>
          <p className="text-xs text-dashboard-text-muted leading-relaxed">{synthesis}</p>
        </div>
      )}

      {/* Blind spots */}
      {blindSpots && blindSpots.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            {t('blindSpots')}
          </h4>
          <ul className="space-y-1">
            {blindSpots.map((s, i) => (
              <li key={i} className="text-xs text-dashboard-text-muted leading-relaxed flex items-start gap-1.5">
                <span className="text-orange-400 mt-0.5 flex-shrink-0">?</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Deep Analysis button */}
      {session?.user ? (
        <Link
          href={`${prefix}/analysis/comparative/${entityType}/${entityId}`}
          className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
        >
          {hasFullReport ? t('viewFullAnalysis') : t('deepAnalysis')}
        </Link>
      ) : (
        <a
          href="/auth/signin"
          className="inline-block text-xs px-3 py-1.5 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
        >
          {t('signInForAnalysis')}
        </a>
      )}
    </div>
  );
}

import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import AnalysisContent from '@/components/AnalysisContent';
import { getNarrativeById } from '@/lib/queries';
import { getTrackLabel, getCountryName } from '@/lib/types';
import type { SignalStats } from '@/lib/types';

export const revalidate = 600;

interface Props {
  params: Promise<{ narrative_id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { narrative_id } = await params;
  const n = await getNarrativeById(narrative_id);
  if (!n) return { title: 'Analysis Not Found' };
  return {
    title: `${n.label} | Analysis`,
    description: n.description || `Narrative analysis: ${n.label}`,
    alternates: { canonical: `/analysis/${narrative_id}` },
  };
}

function MiniBar({ label, count, maxCount }: { label: string; count: number; maxCount: number }) {
  const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-24 text-dashboard-text-muted truncate" title={label}>{label}</span>
      <div className="flex-1 h-1.5 bg-dashboard-border rounded-full overflow-hidden">
        <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-dashboard-text-muted">{count}</span>
    </div>
  );
}

export default async function AnalysisPage({ params }: Props) {
  const { narrative_id } = await params;
  const n = await getNarrativeById(narrative_id);
  if (!n) return notFound();

  const stats: SignalStats | null = n.signal_stats
    ? (typeof n.signal_stats === 'string' ? JSON.parse(n.signal_stats as unknown as string) : n.signal_stats)
    : null;

  const trackLabel = n.track ? getTrackLabel(n.track) : null;

  // Build breadcrumb
  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      {n.centroid_id && n.centroid_name && (
        <>
          <Link href={`/c/${n.centroid_id}`} className="text-blue-400 hover:text-blue-300">
            {n.centroid_name}
          </Link>
          <span className="mx-2">/</span>
        </>
      )}
      {n.centroid_id && n.track && trackLabel && (
        <>
          <Link
            href={`/c/${n.centroid_id}/t/${n.track}`}
            className="text-blue-400 hover:text-blue-300"
          >
            {trackLabel}
          </Link>
          <span className="mx-2">/</span>
        </>
      )}
      {n.event_id && n.event_title && (
        <>
          <Link href={`/events/${n.event_id}`} className="text-blue-400 hover:text-blue-300">
            {n.event_title}
          </Link>
          <span className="mx-2">/</span>
        </>
      )}
      <span>Analysis</span>
    </div>
  );

  // Top publishers for sidebar
  const topPublishers = stats?.top_publishers || [];
  const pubMax = topPublishers[0]?.count || 1;

  // Top persons for sidebar
  const topPersons = stats?.top_persons || [];
  const personMax = topPersons[0]?.count || 1;

  // Language distribution
  const langDist = stats?.language_distribution || {};
  const langTotal = Object.values(langDist).reduce((s, v) => s + v, 0);
  const langSorted = Object.entries(langDist).sort((a, b) => b[1] - a[1]);
  const langVisible = langSorted.filter(([, count]) => (count / (langTotal || 1)) >= 0.01);
  const langHidden = langSorted.length - langVisible.length;

  // Geographic focus (top 5 countries)
  const geoDist = stats?.entity_country_distribution || {};
  const geoSorted = Object.entries(geoDist).sort((a, b) => b[1] - a[1]).slice(0, 5);

  // Sample titles
  const sampleTitles = n.sample_titles
    ? (typeof n.sample_titles === 'string' ? JSON.parse(n.sample_titles as unknown as string) : n.sample_titles)
    : [];

  // Sidebar
  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-4">
      {/* Yellow LLM disclaimer */}
      <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
        <p className="text-xs text-yellow-200 leading-relaxed">
          This analysis is produced by an AI language model (DeepSeek) operating under
          the RAI analytical framework. It is based on the coverage data shown on this
          page. The analysis reflects the available data and may contain omissions or
          misinterpretations. It should be treated as a structured starting point for
          critical thinking, not as a definitive assessment.
        </p>
      </div>

      {/* Narrative meta */}
      {stats && stats.title_count > 0 && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-3">Coverage Stats</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <div className="text-xl font-bold text-dashboard-text">{stats.publisher_count}</div>
              <div className="text-xs text-dashboard-text-muted">Publishers</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-dashboard-text">{stats.language_count}</div>
              <div className="text-xs text-dashboard-text-muted">Languages</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-dashboard-text">{(stats.publisher_hhi * 100).toFixed(1)}%</div>
              <div className="text-xs text-dashboard-text-muted">HHI</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-dashboard-text">{stats.date_range_days}d</div>
              <div className="text-xs text-dashboard-text-muted">Date Span</div>
            </div>
          </div>
        </div>
      )}

      {/* Top Publishers */}
      {topPublishers.length > 0 && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-3">Top Publishers</h3>
          <div className="space-y-1.5">
            {topPublishers.slice(0, 8).map(p => (
              <MiniBar key={p.name} label={p.name} count={p.count} maxCount={pubMax} />
            ))}
          </div>
        </div>
      )}

      {/* Top Persons */}
      {topPersons.length > 0 && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-3">Top Persons</h3>
          <div className="space-y-1.5">
            {topPersons.slice(0, 8).map(p => (
              <MiniBar key={p.name} label={p.name} count={p.count} maxCount={personMax} />
            ))}
          </div>
        </div>
      )}

      {/* Language Distribution */}
      {langVisible.length > 0 && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-2">Languages</h3>
          <div className="flex flex-wrap gap-1">
            {langVisible.map(([lang, count]) => {
              const pct = Math.round((count / langTotal) * 100);
              return (
                <span
                  key={lang}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted"
                  title={`${count} titles (${pct}%)`}
                >
                  {lang.toUpperCase()} {pct}%
                </span>
              );
            })}
            {langHidden > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted">
                +{langHidden} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Geographic Focus */}
      {geoSorted.length > 0 && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-2">Geographic Focus</h3>
          <div className="flex flex-wrap gap-1">
            {geoSorted.map(([code, count]) => (
              <span
                key={code}
                className="text-[10px] px-1.5 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted"
                title={`${count} mentions`}
              >
                {getCountryName(code)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sample Headlines */}
      {sampleTitles.length > 0 && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-2">Sample Headlines</h3>
          <ul className="space-y-2">
            {sampleTitles.slice(0, 10).map((sample: { title: string; publisher: string }, i: number) => (
              <li key={i} className="text-xs flex items-start gap-1.5">
                <span className="text-blue-400 mt-0.5 flex-shrink-0">-</span>
                <div>
                  <span className="text-dashboard-text">{sample.title}</span>
                  <span className="text-dashboard-text-muted ml-1">- {sample.publisher}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {/* Title */}
      <h1 className="text-3xl md:text-4xl font-bold mb-4">{n.label}</h1>

      {/* Moral Frame */}
      {n.moral_frame && (
        <div className="bg-dashboard-border/30 rounded-lg p-4 mb-6">
          <p className="text-base text-dashboard-text leading-relaxed">
            {n.moral_frame}
          </p>
        </div>
      )}

      {/* Description */}
      {n.description && (
        <p className="text-base text-dashboard-text-muted leading-relaxed mb-6">
          {n.description}
        </p>
      )}

      {/* Analysis content (client component) */}
      <AnalysisContent narrative={n} />
    </DashboardLayout>
  );
}

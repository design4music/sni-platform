import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getOutletProfile, getOutletNarrativeFrames } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { getTrackLabel, Track } from '@/lib/types';
import { notFound } from 'next/navigation';
import Link from 'next/link';

export const revalidate = 600;

interface OutletPageProps {
  params: Promise<{ feed_name: string }>;
}

export async function generateMetadata({ params }: OutletPageProps): Promise<Metadata> {
  const { feed_name } = await params;
  const name = decodeURIComponent(feed_name);
  return {
    title: `${name} - Media Profile`,
    description: `Coverage analysis for ${name}: topics, regions, and narrative frames.`,
    alternates: { canonical: `/sources/${feed_name}` },
  };
}

export default async function OutletPage({ params }: OutletPageProps) {
  const { feed_name } = await params;
  const name = decodeURIComponent(feed_name);

  const [profile, narrativeFrames] = await Promise.all([
    getOutletProfile(name),
    getOutletNarrativeFrames(name),
  ]);

  if (!profile) notFound();

  const domain = profile.source_domain || '';
  const logoUrl = getOutletLogoUrl(domain, 64);
  const maxCoverage = profile.centroid_coverage[0]?.count || 1;

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <Link href="/sources" className="text-blue-400 hover:text-blue-300 text-sm">
            &larr; All Sources
          </Link>
          <div className="flex items-center gap-4 mt-4">
            {domain && (
              <img src={logoUrl} alt="" className="w-12 h-12 object-contain rounded" />
            )}
            <div>
              <h1 className="text-3xl md:text-4xl font-bold">{profile.feed_name}</h1>
              <div className="flex flex-wrap items-center gap-3 text-dashboard-text-muted mt-1">
                {profile.country_code && <span>{getCountryName(profile.country_code)}</span>}
                {profile.language_code && (
                  <span className="uppercase text-xs bg-dashboard-border/50 px-2 py-0.5 rounded">
                    {profile.language_code}
                  </span>
                )}
                {domain && (
                  <a
                    href={`https://${domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-sm"
                  >
                    {domain}
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Stats bar */}
          <div className="flex gap-8 mt-6">
            <div>
              <div className="text-2xl font-bold">{profile.article_count.toLocaleString()}</div>
              <div className="text-sm text-dashboard-text-muted">articles</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{profile.centroid_coverage.length}</div>
              <div className="text-sm text-dashboard-text-muted">regions covered</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{profile.top_ctms.length}</div>
              <div className="text-sm text-dashboard-text-muted">active topics</div>
            </div>
          </div>
        </div>

        {/* Coverage by Region */}
        {profile.centroid_coverage.length > 0 && (
          <div className="mb-10">
            <h2 className="text-2xl font-bold mb-4">Coverage by Region</h2>
            <div className="space-y-2">
              {profile.centroid_coverage.slice(0, 25).map(c => {
                const pct = Math.round((c.count / maxCoverage) * 100);
                return (
                  <Link
                    key={c.centroid_id}
                    href={`/c/${c.centroid_id}`}
                    className="flex items-center gap-3 group"
                  >
                    <span className="text-sm w-48 truncate text-dashboard-text group-hover:text-blue-400 transition">
                      {c.label}
                    </span>
                    <div className="flex-1 bg-dashboard-border/30 rounded-full h-5 overflow-hidden">
                      <div
                        className="bg-blue-500/60 h-full rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-sm text-dashboard-text-muted tabular-nums w-16 text-right">
                      {c.count.toLocaleString()}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {/* Top Topics */}
        {profile.top_ctms.length > 0 && (
          <div className="mb-10">
            <h2 className="text-2xl font-bold mb-4">Top Topics</h2>
            <div className="grid gap-3">
              {profile.top_ctms.map(ctm => (
                <Link
                  key={ctm.ctm_id}
                  href={`/c/${ctm.centroid_id}/t/${ctm.track}?month=${ctm.month}`}
                  className="block p-4 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{ctm.label}</span>
                      <span className="text-dashboard-text-muted mx-2">/</span>
                      <span className="text-dashboard-text-muted">
                        {getTrackLabel(ctm.track as Track)}
                      </span>
                    </div>
                    <span className="text-sm text-dashboard-text-muted tabular-nums">
                      {ctm.count} articles
                    </span>
                  </div>
                  <div className="text-xs text-dashboard-text-muted mt-1">{ctm.month}</div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Narrative Frames */}
        {narrativeFrames.length > 0 && (
          <div className="mb-10">
            <h2 className="text-2xl font-bold mb-4">Narrative Frames</h2>
            <p className="text-sm text-dashboard-text-muted mb-4">
              Narrative frames where this outlet is a top contributor
            </p>
            <div className="grid gap-3">
              {narrativeFrames.map((frame, i) => {
                const content = (
                  <div className="p-4 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition">
                    <div className="font-medium">{frame.label}</div>
                    {frame.description && (
                      <p className="text-sm text-dashboard-text-muted mt-1 line-clamp-2">
                        {frame.description}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-dashboard-text-muted">
                      <span className="uppercase bg-dashboard-border/50 px-1.5 py-0.5 rounded">
                        {frame.entity_type}
                      </span>
                      <span>{frame.entity_label}</span>
                      <span>{frame.title_count} titles</span>
                    </div>
                  </div>
                );

                if (frame.entity_type === 'event') {
                  return (
                    <Link key={i} href={`/events/${frame.entity_id}`} className="block">
                      {content}
                    </Link>
                  );
                }
                return <div key={i}>{content}</div>;
              })}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

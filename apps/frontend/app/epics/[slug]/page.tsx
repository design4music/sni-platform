import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import EpicCountries, { CountryGroup } from '@/components/EpicCountries';
import { getEpicBySlug, getEpicEvents, getEpicCentroidBreakdown, getEpicMonths, getEpicFramedNarratives } from '@/lib/queries';
import { EpicEvent, EpicNarrative, EpicCentroidStat, FramedNarrative } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ slug: string }>;
}

// --- Display helpers ---

const SYS_SHORT_LABELS: Record<string, string> = {
  'SYS-TRADE': 'Trade',
  'SYS-DIPLOMACY': 'Diplomacy',
  'SYS-MILITARY': 'Military',
  'SYS-ENERGY': 'Energy',
  'SYS-TECH': 'Technology',
  'SYS-FINANCE': 'Finance',
  'SYS-CLIMATE': 'Climate',
  'SYS-HEALTH': 'Healthcare',
  'SYS-HUMANITARIAN': 'Humanitarian',
  'SYS-MEDIA': 'Media',
};

function getDisplayLabel(centroidId: string, dbLabel: string): string {
  return SYS_SHORT_LABELS[centroidId] || dbLabel;
}

function isSystemCentroid(centroidId: string): boolean {
  return centroidId.startsWith('SYS-') || centroidId.startsWith('NON-STATE-');
}

function sortCountriesFirst<T extends { centroidId?: string; centroid_id?: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const aId = a.centroidId || a.centroid_id || '';
    const bId = b.centroidId || b.centroid_id || '';
    const aSys = isSystemCentroid(aId) ? 1 : 0;
    const bSys = isSystemCentroid(bId) ? 1 : 0;
    return aSys - bSys;
  });
}

// Reuse same icon logic as CentroidBadge in EpicCountries for sidebar
function SysCentroidIcon({ centroidId, size = 14 }: { centroidId: string; size?: number }) {
  const id = centroidId.toUpperCase();
  let path: string;
  if (id.includes('TRADE') || id.includes('FINANCE')) {
    path = 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
  } else if (id.includes('DIPLOMACY')) {
    path = 'M3 7l6 6h6l6-6M9 13l3 4M15 13l-3 4';
  } else if (id.includes('MILITARY')) {
    path = 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z';
  } else if (id.includes('ENERGY')) {
    path = 'M13 10V3L4 14h7v7l9-11h-7z';
  } else if (id.includes('TECH')) {
    path = 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z';
  } else if (id.includes('CLIMATE')) {
    path = 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z';
  } else if (id.includes('HEALTH')) {
    path = 'M12 9v6m-3-3h6M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
  } else if (id.includes('HUMANITARIAN')) {
    path = 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z';
  } else if (id.includes('MEDIA')) {
    path = 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z';
  } else {
    path = 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z';
  }
  return (
    <span
      className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}
    >
      <svg className="text-blue-400 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24" width={size} height={size}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={path} />
      </svg>
    </span>
  );
}

function FlagImg({ iso2, size = 16 }: { iso2: string; size?: number }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <span
      className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 overflow-hidden align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}
    >
      <img
        src={`https://flagcdn.com/w40/${iso2.toLowerCase()}.png`}
        alt={iso2}
        width={size}
        height={Math.round(size * 0.75)}
        className="opacity-70"
        style={{ objectFit: 'contain', filter: 'saturate(0.6) brightness(0.9)' }}
      />
    </span>
  );
}

function SidebarBadge({ stat }: { stat: EpicCentroidStat }) {
  if (stat.iso_codes?.length === 1 && stat.iso_codes[0].length === 2) {
    return <FlagImg iso2={stat.iso_codes[0]} />;
  }
  if (stat.iso_codes && stat.iso_codes.length > 1) {
    return (
      <span className="flex items-center gap-0.5">
        {stat.iso_codes.slice(0, 3).map(iso => (
          <FlagImg key={iso} iso2={iso} size={12} />
        ))}
      </span>
    );
  }
  if (isSystemCentroid(stat.centroid_id)) {
    return <SysCentroidIcon centroidId={stat.centroid_id} />;
  }
  return null;
}

// --- Signal comparison ---

function computeSignalComparison(events: EpicEvent[], anchorTags: string[]) {
  const anchorSet = new Set(anchorTags);
  const centroidTags: Record<string, Record<string, [number, number]>> = {};

  for (const ev of events) {
    if (!ev.tags) continue;
    const cid = ev.centroid_id;
    if (!centroidTags[cid]) centroidTags[cid] = {};
    for (const tag of ev.tags) {
      if (anchorSet.has(tag)) continue;
      if (!centroidTags[cid][tag]) centroidTags[cid][tag] = [0, 0];
      centroidTags[cid][tag][0] += ev.source_batch_count;
      centroidTags[cid][tag][1] += 1;
    }
  }

  const globalFreq: Record<string, number> = {};
  for (const tags of Object.values(centroidTags)) {
    for (const tag of Object.keys(tags)) {
      globalFreq[tag] = (globalFreq[tag] || 0) + 1;
    }
  }

  const sorted = Object.entries(centroidTags).sort((a, b) => {
    const wa = Object.values(a[1]).reduce((s, v) => s + v[0], 0);
    const wb = Object.values(b[1]).reduce((s, v) => s + v[0], 0);
    return wb - wa;
  });

  return { sorted, globalFreq };
}

function groupEventsByCentroid(events: EpicEvent[]) {
  const groups: Record<string, { label: string; events: EpicEvent[] }> = {};
  for (const ev of events) {
    if (!groups[ev.centroid_id]) {
      groups[ev.centroid_id] = { label: ev.centroid_label, events: [] };
    }
    groups[ev.centroid_id].events.push(ev);
  }
  // Sort by total sources descending
  const sorted = Object.entries(groups).sort((a, b) => {
    const sa = a[1].events.reduce((s, e) => s + e.source_batch_count, 0);
    const sb = b[1].events.reduce((s, e) => s + e.source_batch_count, 0);
    return sb - sa;
  });
  // Then stable-sort: countries first, system centroids last
  return sorted.sort((a, b) => {
    const aSys = isSystemCentroid(a[0]) ? 1 : 0;
    const bSys = isSystemCentroid(b[0]) ? 1 : 0;
    return aSys - bSys;
  });
}

// --- Page ---

export default async function EpicDetailPage({ params }: Props) {
  const { slug } = await params;
  const epic = await getEpicBySlug(slug);
  if (!epic) return notFound();

  const [events, centroidBreakdown, epicMonths, framedNarratives] = await Promise.all([
    getEpicEvents(epic.id),
    getEpicCentroidBreakdown(epic.id),
    getEpicMonths(),
    getEpicFramedNarratives(epic.id),
  ]);

  const { sorted: signalData, globalFreq } = computeSignalComparison(events, epic.anchor_tags);
  const groupedEvents = groupEventsByCentroid(events);

  // Sort centroid breakdown: countries first
  const sortedBreakdown = sortCountriesFirst(
    centroidBreakdown.map(s => ({ ...s, centroidId: s.centroid_id }))
  );

  // Build iso_codes lookup
  const isoLookup: Record<string, string[] | null> = {};
  for (const stat of centroidBreakdown) {
    isoLookup[stat.centroid_id] = stat.iso_codes;
  }

  // Build country groups for accordion
  const countryGroups: CountryGroup[] = groupedEvents.map(([centroidId, group]) => ({
    centroidId,
    label: group.label,
    displayLabel: getDisplayLabel(centroidId, group.label),
    events: group.events,
    isoCodes: isoLookup[centroidId] || null,
    summary: epic.centroid_summaries?.[centroidId] || null,
  }));

  const breadcrumb = (
    <nav className="flex items-center gap-2 text-sm text-dashboard-text-muted">
      <Link href="/epics" className="hover:text-dashboard-text transition">
        Epics
      </Link>
      <span>/</span>
      <span className="text-dashboard-text">{epic.title || epic.slug}</span>
    </nav>
  );

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* View by Month */}
      {epicMonths.length > 0 && (
        <div className="hidden lg:block">
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">View by Month</h3>
          <div className="space-y-1">
            {epicMonths.map(m => {
              const isCurrent = m === epic.month;
              return (
                <Link
                  key={m}
                  href={`/epics?month=${m}`}
                  className={`block px-3 py-2 rounded ${
                    isCurrent
                      ? 'bg-blue-600 text-white'
                      : 'text-dashboard-text-muted hover:bg-dashboard-border'
                  }`}
                >
                  {m}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Country coverage */}
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
        <p className="text-xs text-dashboard-text-muted uppercase tracking-wide mb-4">
          Countries ({centroidBreakdown.length})
        </p>
        <nav className="space-y-1">
          {sortedBreakdown.map(stat => (
            <Link
              key={stat.centroid_id}
              href={`/c/${stat.centroid_id}`}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border border border-transparent hover:border-dashboard-border transition-all duration-150"
            >
              <span className="flex items-center gap-2 flex-1 min-w-0">
                <SidebarBadge stat={stat} />
                <span className="text-sm font-medium text-dashboard-text truncate">
                  {getDisplayLabel(stat.centroid_id, stat.centroid_label)}
                </span>
              </span>
              <span className="text-xs text-dashboard-text-muted flex-shrink-0">
                {stat.event_count}
              </span>
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {/* Header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          {epic.title || epic.anchor_tags.join(', ')}
        </h1>
        <p className="text-dashboard-text-muted mb-4">
          {epic.month} | {epic.centroid_count} countries | {epic.event_count} topics | {epic.total_sources} sources
        </p>

        {epic.summary && (
          <p className="text-dashboard-text leading-relaxed mb-4">{epic.summary}</p>
        )}

        <div className="flex flex-wrap gap-1.5">
          {epic.anchor_tags.map(tag => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Timeline */}
      {epic.timeline && (
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <h2 className="text-2xl font-bold mb-4">How It Unfolded</h2>
          <div className="text-dashboard-text leading-relaxed space-y-4">
            {epic.timeline.split('\n\n').map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        </div>
      )}

      {/* What Happened */}
      {epic.narratives && epic.narratives.length > 0 && (
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <h2 className="text-2xl font-bold mb-4">What Happened</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {epic.narratives.map((n: EpicNarrative, i: number) => (
              <div
                key={i}
                className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface"
              >
                <h3 className="font-semibold mb-2">{n.title}</h3>
                <p className="text-sm text-dashboard-text-muted leading-relaxed">
                  {n.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* How It Was Framed */}
      {framedNarratives.length > 0 && (
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <h2 className="text-2xl font-bold mb-4">How It Was Framed</h2>
          <p className="text-sm text-dashboard-text-muted mb-4">
            Contested narratives extracted from {framedNarratives.reduce((sum, n) => sum + n.title_count, 0)} headlines.
            Sources shown over-index on each frame compared to their baseline coverage.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {framedNarratives.map((n: FramedNarrative) => (
              <div
                key={n.id}
                className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold">{n.label}</h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted flex-shrink-0">
                    {n.title_count} titles
                  </span>
                </div>
                {n.moral_frame && (
                  <p className="text-sm text-dashboard-text-muted leading-relaxed mb-3">
                    {n.moral_frame}
                  </p>
                )}
                {/* Over-indexed sources */}
                {n.top_sources && n.top_sources.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs text-dashboard-text-muted mr-2">Favored by:</span>
                    <div className="inline-flex flex-wrap gap-1">
                      {n.top_sources.slice(0, 4).map((src, i) => (
                        <span
                          key={i}
                          className="text-xs px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20"
                        >
                          {src}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {/* Proportional sources */}
                {n.proportional_sources && n.proportional_sources.length > 0 && (
                  <div>
                    <span className="text-xs text-dashboard-text-muted mr-2">Broad coverage:</span>
                    <div className="inline-flex flex-wrap gap-1">
                      {n.proportional_sources.slice(0, 3).map((src, i) => (
                        <span
                          key={i}
                          className="text-xs px-1.5 py-0.5 rounded bg-gray-500/10 text-gray-400 border border-gray-500/20"
                        >
                          {src}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Coverage by Country */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h2 className="text-2xl font-bold mb-4">Coverage by Country</h2>
        <EpicCountries groups={countryGroups} />
      </div>

      {/* Signal Comparison (collapsed) */}
      {signalData.length > 0 && (
        <details className="group">
          <summary className="cursor-pointer flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition-colors list-none">
            <span
              className="text-dashboard-text-muted transition-transform duration-200 group-open:rotate-90"
            >
              &#9656;
            </span>
            <span className="text-lg font-semibold text-dashboard-text">Signal Comparison</span>
            <span className="text-sm text-dashboard-text-muted ml-auto">
              Tag distribution across countries
            </span>
          </summary>
          <div className="mt-4 pl-4">
            <p className="text-sm text-dashboard-text-muted mb-4">
              Top tags per country. * = distinctive (appears in 3 or fewer countries).
            </p>
            <div className="space-y-2 font-mono text-sm">
              {signalData.map(([centroidId, tags]) => {
                const top = Object.entries(tags)
                  .sort((a, b) => b[1][0] - a[1][0])
                  .slice(0, 6);
                if (top.length === 0) return null;
                return (
                  <div key={centroidId} className="flex gap-4">
                    <span className="text-dashboard-text-muted w-48 flex-shrink-0 truncate">
                      {centroidId}
                    </span>
                    <span className="text-dashboard-text">
                      {top.map(([tag, [, count]]) => {
                        const marker = (globalFreq[tag] || 0) <= 3 ? '*' : '';
                        return `${marker}${tag}(${count})`;
                      }).join('  ')}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </details>
      )}
    </DashboardLayout>
  );
}

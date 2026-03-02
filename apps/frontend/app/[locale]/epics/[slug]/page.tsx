import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import EpicCountries, { CountryGroup } from '@/components/EpicCountries';
import NarrativeCards from '@/components/NarrativeOverlay';
import { getEpicBySlug, getEpicEvents, getEpicMonths, getEpicFramedNarratives, getTopSignalsForEpic } from '@/lib/queries';
import { EpicEvent, EpicNarrative, SignalType, getCentroidLabel } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { ensureDE } from '@/lib/lazy-translate';
import TranslationNotice from '@/components/TranslationNotice';

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const t = await getTranslations('epics');
  const epic = await getEpicBySlug(slug, locale);
  if (!epic) return { title: t('storyNotFound') };
  const title = epic.title || epic.anchor_tags?.join(', ') || t('crossCountryStory');
  return {
    title,
    description: t('detailMetaDescription', { title }),
    alternates: { canonical: `/epics/${slug}` },
  };
}

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

// --- Display helpers ---

function formatMonthLabel(monthStr: string, loc: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', { month: 'long', year: 'numeric' });
}

const SYS_LABEL_KEYS: Record<string, string> = {
  'SYS-TRADE': 'sysTrade',
  'SYS-DIPLOMACY': 'sysDiplomacy',
  'SYS-MILITARY': 'sysMilitary',
  'SYS-ENERGY': 'sysEnergy',
  'SYS-TECH': 'sysTechnology',
  'SYS-FINANCE': 'sysFinance',
  'SYS-CLIMATE': 'sysClimate',
  'SYS-HEALTH': 'sysHealthcare',
  'SYS-HUMANITARIAN': 'sysHumanitarian',
  'SYS-MEDIA': 'sysMedia',
};

function getDisplayLabel(centroidId: string, dbLabel: string, t: (key: string) => string, tCentroids?: (key: string) => string): string {
  const key = SYS_LABEL_KEYS[centroidId];
  if (key) return t(key);
  return getCentroidLabel(centroidId, dbLabel, tCentroids);
}

function isSystemCentroid(centroidId: string): boolean {
  return centroidId.startsWith('SYS-') || centroidId.startsWith('NON-STATE-');
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
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('epics');
  const tCommon = await getTranslations('common');
  const tNav = await getTranslations('nav');
  const tCentroids = await getTranslations('centroids');
  const intlLocale = await getLocale();
  let epic = await getEpicBySlug(slug, locale);
  if (!epic) return notFound();

  // Lazy-translate epic fields for DE users
  if (locale === 'de') {
    const de = await ensureDE('epics', 'id', epic.id, [
      { src: 'title', dest: 'title_de', text: epic.title || '', style: 'headline' },
      { src: 'summary', dest: 'summary_de', text: epic.summary || '' },
      { src: 'timeline', dest: 'timeline_de', text: epic.timeline || '' },
    ]);
    if (de.title) epic = { ...epic, title: de.title };
    if (de.summary) epic = { ...epic, summary: de.summary };
    if (de.timeline) epic = { ...epic, timeline: de.timeline };
  }

  const [events, epicMonths, framedNarratives, epicSignals] = await Promise.all([
    getEpicEvents(epic.id, locale),
    getEpicMonths(),
    getEpicFramedNarratives(epic.id),
    getTopSignalsForEpic(epic.id, 12),
  ]);

  const { sorted: signalData, globalFreq } = computeSignalComparison(events, epic.anchor_tags);
  const groupedEvents = groupEventsByCentroid(events);

  // Build iso_codes lookup from events
  const isoLookup: Record<string, string[] | null> = {};
  for (const ev of events) {
    if (!isoLookup[ev.centroid_id]) {
      isoLookup[ev.centroid_id] = ev.iso_codes || null;
    }
  }

  // Build country groups for accordion
  const countryGroups: CountryGroup[] = groupedEvents.map(([centroidId, group]) => ({
    centroidId,
    label: group.label,
    displayLabel: getDisplayLabel(centroidId, group.label, t, tCentroids),
    events: group.events,
    isoCodes: isoLookup[centroidId] || null,
    summary: epic.centroid_summaries?.[centroidId] || null,
  }));

  const breadcrumb = (
    <Link
      href="/epics"
      className="text-blue-400 hover:text-blue-300 text-sm"
    >
      &larr; {tNav('epics')}
    </Link>
  );

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* View by Month */}
      {epicMonths.length > 0 && (
        <div className="hidden lg:block">
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">{tNav('viewByMonth')}</h3>
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
                  {formatMonthLabel(m, intlLocale)}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* How It Was Framed - interactive cards with overlay */}
      <NarrativeCards narratives={framedNarratives} />
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {locale === 'de' && <TranslationNotice message={tCommon('translatedNotice')} />}
      {/* Header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          {epic.title || epic.anchor_tags.join(', ')}
        </h1>
        <p className="text-dashboard-text-muted mb-4">
          {t('detailStats', { month: formatMonthLabel(epic.month, intlLocale), countries: epic.centroid_count, events: epic.event_count, sources: epic.total_sources })}
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
          <h2 className="text-2xl font-bold mb-4">{t('howItUnfolded')}</h2>
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
          <h2 className="text-2xl font-bold mb-4">{t('whatHappened')}</h2>
          <div className="space-y-4">
            {epic.narratives.map((n: EpicNarrative, i: number) => (
              <div key={i}>
                <h3 className="font-semibold text-sm mb-1">{n.title}</h3>
                <p className="text-sm text-dashboard-text-muted leading-relaxed">
                  {n.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Signals */}
      {epicSignals.length > 0 && (
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <h2 className="text-2xl font-bold mb-4">{t('keySignals')}</h2>
          <div className="flex flex-wrap gap-2">
            {epicSignals.map(s => (
              <Link
                key={`${s.signal_type}-${s.value}`}
                href={`/signals/${s.signal_type}/${encodeURIComponent(s.value)}`}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-sm border border-dashboard-border bg-dashboard-surface hover:border-blue-500/50 transition"
              >
                <span className="text-dashboard-text">{s.value}</span>
                <span className="text-xs text-dashboard-text-muted">{s.event_count}</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Coverage by Country */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h2 className="text-2xl font-bold mb-4">{t('coverageByCountry')}</h2>
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
            <span className="text-lg font-semibold text-dashboard-text">{t('signalComparison')}</span>
            <span className="text-sm text-dashboard-text-muted ml-auto">
              {t('tagDistribution')}
            </span>
          </summary>
          <div className="mt-4 pl-4">
            <p className="text-sm text-dashboard-text-muted mb-4">
              {t('topTagsNote')}
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

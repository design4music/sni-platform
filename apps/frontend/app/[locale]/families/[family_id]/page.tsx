import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import { getFamilyById, getFamilyEvents } from '@/lib/queries';
import { getTrackLabel, getCentroidLabel, getCountryName, getIsoFromBucketKey, Track } from '@/lib/types';
import { setRequestLocale, getTranslations } from 'next-intl/server';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; family_id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, family_id } = await params;
  const family = await getFamilyById(family_id, locale);
  if (!family) return { title: 'Family not found' };
  return { title: family.title };
}

export default async function FamilyPage({ params }: Props) {
  const { locale, family_id } = await params;
  setRequestLocale(locale);
  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');

  const [family, events] = await Promise.all([
    getFamilyById(family_id, locale),
    getFamilyEvents(family_id, locale),
  ]);

  if (!family) notFound();

  const centroidLabel = getCentroidLabel(family.centroid_id, family.centroid_label, tCentroids);
  const trackLabel = getTrackLabel(family.track as Track, tTracks);
  const totalSources = events.reduce((s, e) => s + e.source_batch_count, 0);

  // Group events by country for display
  const byCountry = new Map<string, typeof events>();
  for (const ev of events) {
    const key = ev.event_type === 'domestic' ? 'Domestic' : (ev.bucket_key || 'Other');
    if (!byCountry.has(key)) byCountry.set(key, []);
    byCountry.get(key)!.push(ev);
  }
  const countryGroups = [...byCountry.entries()]
    .map(([key, evts]) => ({
      key,
      label: key === 'Domestic' ? centroidLabel : getCountryName(key),
      isoCode: key === 'Domestic' ? null : getIsoFromBucketKey(key),
      events: evts,
      totalSrc: evts.reduce((s, e) => s + e.source_batch_count, 0),
    }))
    .sort((a, b) => b.totalSrc - a.totalSrc);

  return (
    <DashboardLayout centroidLabel={centroidLabel} centroidId={family.centroid_id}>
      <div className="mb-6">
        <Link
          href={`/c/${family.centroid_id}/t/${family.track}?month=${family.month}`}
          className="text-blue-400 hover:text-blue-300 text-sm"
        >
          &larr; {centroidLabel}: {trackLabel}
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-2">{family.title}</h1>
      <p className="text-dashboard-text-muted mb-6">
        {events.length} topics | {totalSources} sources | {family.month}
      </p>

      {family.summary && (
        <div className="mb-8 text-lg leading-relaxed">
          <p>{family.summary}</p>
        </div>
      )}

      <div className="space-y-6">
        {countryGroups.map(group => (
          <div key={group.key}>
            {countryGroups.length > 1 && (
              <div className="flex items-center gap-2 mb-3">
                {group.isoCode && (
                  <img src={`https://flagcdn.com/20x15/${group.isoCode.toLowerCase()}.png`}
                    alt="" width={20} height={15} />
                )}
                <h3 className="text-lg font-semibold text-dashboard-text">{group.label}</h3>
                <span className="text-xs text-dashboard-text-muted">{group.totalSrc} sources</span>
              </div>
            )}
            <div className="space-y-1">
              {group.events.map(ev => {
                const dateStr = ev.date
                  ? new Date(ev.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                  : '';
                return (
                  <Link key={ev.id} href={`/events/${ev.id}`}
                    className="flex items-start gap-3 py-2 px-3 rounded hover:bg-dashboard-surface-hover transition-colors group">
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-dashboard-text group-hover:text-blue-400 line-clamp-2">
                        {ev.title}
                      </span>
                      {ev.summary && (
                        <p className="text-xs text-dashboard-text-muted mt-0.5 line-clamp-1">{ev.summary}</p>
                      )}
                    </div>
                    <div className="text-xs text-dashboard-text-muted whitespace-nowrap flex-shrink-0 text-right">
                      {dateStr && <div>{dateStr}</div>}
                      <div>{ev.source_batch_count} src</div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
}

import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import NarrativeCards from '@/components/NarrativeOverlay';
import RaiSidebar from '@/components/RaiSidebar';
import ExpandableTitles from '@/components/ExpandableTitles';
import SignalDashboard from '@/components/SignalDashboard';
import RelatedStories from '@/components/RelatedStories';
import { getEventById, getEventTitles, getFramedNarratives, getRelatedEvents } from '@/lib/queries';
import { getTrackLabel } from '@/lib/types';

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { event_id } = await params;
  const event = await getEventById(event_id);
  if (!event) return { title: 'Event Not Found' };
  const title = event.title || 'Event Detail';
  return {
    title,
    description: event.summary ? `${event.summary.slice(0, 155)}...` : `News analysis: ${title}. Narrative frames, source coverage, and media signals.`,
    alternates: { canonical: `/events/${event_id}` },
  };
}

interface Props {
  params: Promise<{ event_id: string }>;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function PerspectiveBadge({ centroidId, label, track, month }: {
  centroidId: string; label: string; track: string; month: string;
}) {
  // Extract ISO code from centroid_id like "MIDEAST-IRAN" -> "IR" or "AMERICAS-USA" -> "US"
  const parts = centroidId.split('-');
  const isoCode = parts.length > 1 ? parts[parts.length - 1] : null;
  // Map common codes
  const isoMap: Record<string, string> = {
    USA: 'US', IRAN: 'IR', ISRAEL: 'IL', TURKEY: 'TR', CHINA: 'CN',
    RUSSIA: 'RU', INDIA: 'IN', BRAZIL: 'BR', GERMANY: 'DE', FRANCE: 'FR',
    JAPAN: 'JP', UK: 'GB', KOREA: 'KR', AUSTRALIA: 'AU', CANADA: 'CA',
  };
  const iso2 = isoCode ? (isoMap[isoCode] || (isoCode.length === 2 ? isoCode : null)) : null;

  return (
    <Link
      href={`/c/${centroidId}/t/${track}?month=${month}`}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 hover:border-blue-500/40 transition-colors"
    >
      {iso2 && (
        <img
          src={`https://flagcdn.com/w40/${iso2.toLowerCase()}.png`}
          alt={iso2}
          width={20}
          height={15}
          className="opacity-80"
          style={{ objectFit: 'contain', filter: 'saturate(0.7)' }}
        />
      )}
      <span className="text-sm font-medium text-blue-400">{label}</span>
      <span className="text-xs text-blue-400/60">{getTrackLabel(track)}</span>
    </Link>
  );
}

export default async function EventDetailPage({ params }: Props) {
  const { event_id } = await params;

  const event = await getEventById(event_id);
  if (!event) return notFound();

  const [titles, narratives, relatedEvents] = await Promise.all([
    getEventTitles(event_id),
    getFramedNarratives('event', event_id),
    getRelatedEvents(event_id, event.centroid_id),
  ]);

  const trackLabel = getTrackLabel(event.track);

  // Signal stats are the same across all narratives for an event
  // Only use stats if they have full Tier 1 data (title_count), not just extraction markers
  const rawStats = narratives.length > 0 ? narratives[0].signal_stats : null;
  const signalStats = rawStats?.title_count ? rawStats : null;
  const raiSignals = narratives.length > 0 ? narratives[0].rai_signals : null;

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      <Link href={`/c/${event.centroid_id}`} className="text-blue-400 hover:text-blue-300">
        {event.centroid_label}
      </Link>
      <span className="mx-2">/</span>
      <Link
        href={`/c/${event.centroid_id}/t/${event.track}?month=${event.month}`}
        className="text-blue-400 hover:text-blue-300"
      >
        {trackLabel}
      </Link>
      <span className="mx-2">/</span>
      <span>{event.title || 'Event'}</span>
    </div>
  );

  const sidebar = (narratives.length > 0 || raiSignals) ? (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Narrative Frames */}
      {narratives.length > 0 && (
        <NarrativeCards narratives={narratives} />
      )}

      {/* Coverage Assessment */}
      {raiSignals && (
        <RaiSidebar signals={raiSignals} stats={signalStats} />
      )}
    </div>
  ) : undefined;

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {/* Perspective badge */}
      <div className="mb-4">
        <PerspectiveBadge
          centroidId={event.centroid_id}
          label={event.centroid_label}
          track={event.track}
          month={event.month}
        />
      </div>

      {/* Header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          {event.title || 'Event Detail'}
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-dashboard-text-muted">
          <span>{formatDate(event.date)}</span>
          {event.last_active && event.last_active !== event.date && (
            <span>- {formatDate(event.last_active)}</span>
          )}
          <span className="text-xs px-2 py-0.5 rounded bg-dashboard-border">
            {event.source_batch_count} sources
          </span>
        </div>
        {event.tags && event.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {event.tags.map((tag, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Summary */}
      {event.summary && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Summary</h2>
          <div className="text-lg leading-relaxed space-y-4">
            {event.summary.split('\n\n').map((para, i) => (
              <p key={i}>{para.trim()}</p>
            ))}
          </div>
        </div>
      )}

      {/* Topic Stats */}
      {signalStats && (
        <div className="mb-8">
          <SignalDashboard stats={signalStats} />
        </div>
      )}

      {/* Related Coverage */}
      <RelatedStories events={relatedEvents} />

      {/* Source Headlines */}
      {titles.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Source Headlines</h2>
          <ExpandableTitles titles={titles} />
        </div>
      )}
    </DashboardLayout>
  );
}

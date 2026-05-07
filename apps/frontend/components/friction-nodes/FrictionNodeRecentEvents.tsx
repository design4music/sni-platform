import Link from 'next/link';
import type { FnRecentEvent } from '@/lib/friction-nodes-shared';

interface Props {
  events: FnRecentEvent[];
  locale: string;
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    sources: string;
    importance: string;
    none: string;
  };
}

function formatDate(dateStr: string, locale: string): string {
  // events_v3.date returns YYYY-MM-DD; pin to UTC-noon to dodge TZ slip.
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function importanceBadge(score: number | null): { label: string; cls: string } | null {
  if (score == null) return null;
  if (score >= 0.5) return { label: 'high', cls: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
  return null;
}

/**
 * Recent events on the FN — the FACTUAL layer that the narrative cards
 * interpret. Orders by importance DESC then date DESC. Each row links to
 * the existing /events/[id] detail page.
 */
export default function FrictionNodeRecentEvents({ events, locale, labels }: Props) {
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>
      {events.length === 0 ? (
        <div className="text-sm text-dashboard-text-muted italic">{labels.none}</div>
      ) : (
        <div className="space-y-2">
          {events.map((ev) => {
            const importance = importanceBadge(ev.importance);
            return (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
              >
                <span className="text-sm text-dashboard-text md:flex-1 md:min-w-0 leading-snug">
                  {ev.title}
                </span>
                <div className="flex items-center gap-2 shrink-0">
                  {importance && (
                    <span
                      className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${importance.cls}`}
                      title={`${labels.importance}: ${ev.importance?.toFixed(2)}`}
                    >
                      {importance.label}
                    </span>
                  )}
                  <span
                    className="text-[11px] text-dashboard-text-muted tabular-nums"
                    title={`${ev.source_count} ${labels.sources}`}
                  >
                    {ev.source_count} {labels.sources}
                  </span>
                  <span className="text-[11px] text-dashboard-text-muted font-mono tabular-nums">
                    {formatDate(ev.date, locale)}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </section>
  );
}

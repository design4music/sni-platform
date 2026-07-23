import Link from 'next/link';
import { getLocale } from 'next-intl/server';
import { getNarrativesForEvent } from '@/lib/queries';

interface Props {
  eventId: string;
  /** The event's own centroid. When provided, narratives whose actor is a
   *  different centroid get a "from {actor}" foreign-framing chip — same
   *  affordance as ActiveNarrativesSection on centroid pages. */
  centroidId?: string;
  variant?: 'inline' | 'sidebar';
}

export default async function EventNarrativeBadges({ eventId, centroidId, variant = 'inline' }: Props) {
  const locale = await getLocale();
  const links = await getNarrativesForEvent(eventId, locale);
  if (links.length === 0) return null;

  const fromWord = locale === 'de' ? 'von' : 'from';

  function ForeignActorChip({ label }: { label: string }) {
    return (
      <span className="ml-1.5 inline-flex items-center px-1.5 py-0 rounded-sm text-[10px]
                       bg-amber-500/10 border border-amber-500/30 text-amber-400 align-middle">
        {fromWord} {label}
      </span>
    );
  }

  function isForeign(link: typeof links[number]): boolean {
    return Boolean(centroidId && link.actor_centroid && link.actor_centroid !== centroidId);
  }

  if (variant === 'sidebar') {
    return (
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-dashboard-text">Strategic Narratives</h3>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          Geopolitical narratives this event connects to
        </p>
        <div className="space-y-2.5">
          {links.map(link => (
            <Link
              key={link.narrative_id}
              href={`/narratives/${link.narrative_id}`}
              className="block group"
            >
              <span className="flex gap-2">
                <span className="text-purple-400/70 shrink-0 mt-0.5">&bull;</span>
                <span className="text-sm leading-snug text-dashboard-text group-hover:text-purple-400 transition">
                  {link.narrative_name}
                </span>
              </span>
              {isForeign(link) && link.actor_label && (
                <span className="block pl-4 mt-0.5 text-[11px] text-dashboard-text-muted">
                  {fromWord} {link.actor_label}
                </span>
              )}
            </Link>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5 mt-3">
      {links.map(link => (
        <Link
          key={link.narrative_id}
          href={`/narratives/${link.narrative_id}`}
          className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border transition ${
            link.confidence >= 0.8
              ? 'bg-purple-500/10 border-purple-500/30 text-purple-400 hover:border-purple-500/50'
              : 'bg-slate-500/10 border-slate-500/30 text-slate-400 hover:border-slate-500/50'
          }`}
        >
          <span className="truncate max-w-[200px]">{link.narrative_name}</span>
          {isForeign(link) && link.actor_label && (
            <ForeignActorChip label={link.actor_label} />
          )}
        </Link>
      ))}
    </div>
  );
}

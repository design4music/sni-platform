import Link from 'next/link';
import { getNarrativesForEvent } from '@/lib/queries';

interface Props {
  eventId: string;
  variant?: 'inline' | 'sidebar';
}

export default async function EventNarrativeBadges({ eventId, variant = 'inline' }: Props) {
  const links = await getNarrativesForEvent(eventId);
  if (links.length === 0) return null;

  if (variant === 'sidebar') {
    return (
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-dashboard-text">Strategic Narratives</h3>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          Geopolitical narratives this event connects to
        </p>
        <div className="space-y-1.5">
          {links.map(link => (
            <Link
              key={link.narrative_id}
              href={`/narratives/${link.narrative_id}`}
              className="flex items-center gap-2 text-xs hover:text-purple-400 transition"
            >
              <span className="text-purple-400/70 shrink-0">&bull;</span>
              <span className="text-dashboard-text truncate">{link.narrative_name}</span>
              {link.actor_label && (
                <span className="text-dashboard-text-muted shrink-0">{link.actor_label}</span>
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
        </Link>
      ))}
    </div>
  );
}

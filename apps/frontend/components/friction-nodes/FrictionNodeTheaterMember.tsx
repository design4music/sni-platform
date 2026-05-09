import Link from 'next/link';
import type { TheaterMemberFn } from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';

interface Props {
  member: TheaterMemberFn;
  locale: string;
  isDe: boolean;
}

/**
 * One card per atomic FN inside a theater. Shows name, editorial summary
 * (clamped), event count, and stance bricks (small) for the FN's
 * narratives. Click anywhere on the card to open the atomic FN page.
 */
export default function FrictionNodeTheaterMember({ member, locale, isDe }: Props) {
  const totalAttributed = member.stances.reduce((acc, s) => acc + s.match_count, 0);
  return (
    <Link
      href={`/${locale}/friction-nodes/${member.id}`}
      className="block rounded-lg border border-dashboard-border bg-dashboard-card hover:border-blue-400/60 transition p-4 group"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="text-base font-semibold text-dashboard-text leading-tight group-hover:text-blue-300 transition">
          {member.name}
        </h3>
      </div>
      {member.editorial_summary && (
        <p className="text-sm text-dashboard-text-muted leading-snug line-clamp-3 mb-3">
          {member.editorial_summary}
        </p>
      )}

      {/* Stance bricks (mini) */}
      {member.stances.length > 0 && (
        <div className="grid grid-cols-2 gap-1.5 mb-3">
          {member.stances.map((s) => {
            const isStandBy = s.narrative_type === 'stand_by';
            return (
              <div
                key={s.narrative_id}
                className="rounded text-white text-[11px] px-2 py-1.5 leading-tight flex items-baseline justify-between gap-2"
                style={{
                  backgroundColor: colorForNarrative(s.display_order, isStandBy),
                  opacity: isStandBy ? 1 : 0.85,
                }}
                title={`${s.label} — ${s.match_count} ${isDe ? 'Schlagzeilen' : 'titles'}`}
              >
                <span className="line-clamp-1 font-medium">{s.label}</span>
                <span className="tabular-nums opacity-90">{s.match_count}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-dashboard-text-muted">
        <span>
          <span className="uppercase tracking-wider mr-1">
            {isDe ? 'Ereignisse' : 'Events'}:
          </span>
          <span className="text-dashboard-text">{member.event_count}</span>
        </span>
        <span>
          <span className="uppercase tracking-wider mr-1">
            {isDe ? 'Schlagzeilen' : 'Headlines'}:
          </span>
          <span className="text-dashboard-text">{totalAttributed}</span>
        </span>
      </div>
    </Link>
  );
}

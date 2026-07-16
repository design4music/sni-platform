import Link from 'next/link';
import type { TheaterMemberFn } from '@/lib/friction-nodes-shared';
import { colorForNarrative, filterNarrativesForDisplay } from '@/lib/friction-nodes-shared';

interface Props {
  member: TheaterMemberFn;
  locale: string;
  isDe: boolean;
  /** True when this card represents the FN page the reader is already on:
   *  rendered muted and non-clickable instead of as a Link. */
  isCurrent?: boolean;
}

/**
 * One card per atomic FN inside a theater. Shows name, editorial summary
 * (clamped), headline count, and stance bricks (small) for the FN's
 * narratives. Click anywhere on the card to open the atomic FN page --
 * unless it's the FN already being viewed (isCurrent), which renders muted
 * and inert. Stance bricks use the same first-two-always/3rd-if->=5 display
 * filter as the full narrative cards (filterNarrativesForDisplay).
 */
export default function FrictionNodeTheaterMember({ member, locale, isDe, isCurrent }: Props) {
  const displayStances = filterNarrativesForDisplay(member.stances);
  const totalAttributed = member.stances.reduce((acc, s) => acc + s.match_count, 0);

  const cardContent = (
    <>
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3
          className={`text-base font-semibold leading-tight transition ${
            isCurrent ? 'text-dashboard-text-muted' : 'text-dashboard-text group-hover:text-blue-300'
          }`}
        >
          {member.name}
        </h3>
        {isCurrent && (
          <span className="shrink-0 text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border border-dashboard-border text-dashboard-text-muted">
            {isDe ? 'Aktuell' : 'Current'}
          </span>
        )}
      </div>
      {member.editorial_summary && (
        <p className="text-sm text-dashboard-text-muted leading-snug line-clamp-3 mb-3">
          {member.editorial_summary}
        </p>
      )}

      {/* Stance bricks (mini) */}
      {displayStances.length > 0 && (
        <div className="grid grid-cols-2 gap-1.5 mb-3">
          {displayStances.map((s) => (
            <div
              key={s.narrative_id}
              className="rounded text-white text-[11px] px-2 py-1.5 leading-tight flex items-baseline justify-between gap-2"
              style={{
                backgroundColor: colorForNarrative(s.stance),
                opacity: isCurrent ? 0.5 : 0.85,
              }}
              title={`${s.label} — ${s.match_count} ${isDe ? 'Schlagzeilen' : 'titles'}`}
            >
              <span className="line-clamp-1 font-medium">{s.label}</span>
              <span className="tabular-nums opacity-90">{s.match_count}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-dashboard-text-muted">
        <span>
          <span className="uppercase tracking-wider mr-1">
            {isDe ? 'Schlagzeilen' : 'Headlines'}:
          </span>
          <span className="text-dashboard-text">{totalAttributed}</span>
        </span>
      </div>
    </>
  );

  if (isCurrent) {
    return (
      <div
        aria-current="page"
        className="block rounded-lg border border-dashboard-border bg-dashboard-card/50 p-4 opacity-60 cursor-default select-text"
      >
        {cardContent}
      </div>
    );
  }

  return (
    <Link
      href={`/${locale}/friction-nodes/${member.id}`}
      className="block rounded-lg border border-dashboard-border bg-dashboard-card hover:border-blue-400/60 transition p-4 group"
    >
      {cardContent}
    </Link>
  );
}

import type { NarrativeOnFn } from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';

interface Props {
  narratives: NarrativeOnFn[];
  locale: string;
  /** Translation strings (passed in to keep the component server-safe and locale-flexible). */
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    titles: string;
  };
}

/**
 * Brick row at the top of the FN page: one large pill per linked narrative,
 * coloured by the narrative's display_order slot. Mirrors the visual rhythm
 * of OutletStanceBricks but with FN/narrative semantics.
 *
 * Each brick anchors to the corresponding detailed card below.
 */
export default function FrictionNodeNarrativeBricks({
  narratives,
  locale,
  labels,
}: Props) {
  if (narratives.length === 0) return null;

  // Background opacity scales with match volume so heavily-covered
  // coalitions pop against lighter ones.
  const max = Math.max(...narratives.map((n) => n.match_count), 1);
  const opacityFor = (n: number) => {
    if (n <= 0) return 0.55;
    const t = Math.log10(n + 1) / Math.log10(max + 1);
    return 0.55 + 0.4 * t;
  };

  return (
    <section className="mb-8">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        {narratives.map((n) => {
          const hue = colorForNarrative(n.stance);
          const anchorId = `narrative-${n.narrative_id}`;
          return (
            <a
              key={n.narrative_id}
              href={`#${anchorId}`}
              className="block rounded-lg p-3 transition hover:ring-2 hover:ring-blue-400/60 text-white relative overflow-hidden min-h-[6.5rem] flex flex-col"
              style={{ backgroundColor: hue, opacity: opacityFor(n.match_count) }}
              title={`${n.stance_label} — ${n.match_count} ${labels.titles}`}
            >
              <div className="text-base font-semibold leading-tight mb-2 line-clamp-2">
                {n.stance_label}
              </div>
              <div className="mt-auto flex items-baseline justify-between gap-2">
                <span className="text-3xl font-bold tabular-nums leading-none">
                  {n.match_count}
                </span>
                <span className="text-[11px] tabular-nums opacity-90">
                  {labels.titles}
                </span>
              </div>
            </a>
          );
        })}
      </div>
    </section>
  );
}

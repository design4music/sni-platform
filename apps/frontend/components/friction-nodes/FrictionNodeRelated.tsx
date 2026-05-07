import Link from 'next/link';
import type { RelatedFn } from '@/lib/friction-nodes-shared';

interface Props {
  related: RelatedFn[];
  locale: string;
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    sharedNarratives: string;
    none: string;
  };
}

/**
 * Other FNs sharing >=2 narratives with this FN. The "theater grouping"
 * concept: when several FNs are contested by overlapping narrative
 * coalitions, they form a navigable cluster (e.g. Iran nuclear + Bab el-Mandeb
 * + Israel-Palestine all hosting the multipolar + existential-threat coalitions).
 *
 * With one FN in the system this is empty; structure stays so the feature
 * lights up as more FNs land.
 */
export default function FrictionNodeRelated({ related, locale, labels }: Props) {
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>
      {related.length === 0 ? (
        <div className="text-sm text-dashboard-text-muted italic px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border border-dashed">
          {labels.none}
        </div>
      ) : (
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {related.map((r) => (
            <li key={r.id}>
              <Link
                href={`/friction-nodes/${r.id}`}
                className="flex items-center justify-between gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
              >
                <span className="text-sm font-medium text-dashboard-text truncate">
                  {r.name}
                </span>
                <span className="text-[11px] text-dashboard-text-muted tabular-nums shrink-0">
                  {r.shared_narratives} {labels.sharedNarratives}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

import Link from 'next/link';
import type { RelatedFn } from '@/lib/friction-nodes-shared';

interface Props {
  related: RelatedFn[];
  locale: string;
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    none: string;
  };
}

/**
 * Sibling atomic conflicts in the same theater. Provides lateral navigation
 * between atomic conflicts under one umbrella theater.
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
                href={`/${locale}/friction-nodes/${r.id}`}
                className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
              >
                <span className="text-sm font-medium text-dashboard-text truncate">
                  {r.name}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

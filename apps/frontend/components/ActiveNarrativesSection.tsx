import Link from 'next/link';
import { getTranslations, getLocale } from 'next-intl/server';
import { getCentroidLabel } from '@/lib/types';

interface ActiveNarrative {
  id: string;
  name: string;
  event_count: number;
  actor_centroid: string | null;
}

interface Props {
  centroidId: string;
  narratives: ActiveNarrative[];
}

export default async function ActiveNarrativesSection({
  centroidId,
  narratives,
}: Props) {
  const tCentroids = await getTranslations('centroids');
  const locale = await getLocale();

  if (narratives.length === 0) return null;

  return (
    <section>
      <h2 className="text-2xl font-bold mb-4">
        {locale === 'de' ? 'Aktive Narrative' : 'Active Narratives'}
      </h2>
      <ul className="space-y-2">
        {narratives.map(n => {
          const foreign = n.actor_centroid && n.actor_centroid !== centroidId;
          const actorLabel = foreign
            ? getCentroidLabel(n.actor_centroid!, n.actor_centroid!, tCentroids)
            : null;
          return (
            <li key={n.id}>
              <Link
                href={`/narratives/${n.id}`}
                className="flex items-start gap-2 text-sm text-dashboard-text hover:text-blue-400 transition group"
              >
                <span className="text-dashboard-text-muted tabular-nums text-[11px] pt-0.5 shrink-0 w-6 text-right">
                  {n.event_count}
                </span>
                <span className="flex-1 min-w-0 leading-snug">
                  {n.name}
                  {actorLabel && (
                    <span className="ml-1.5 inline-flex items-center px-1.5 py-0 rounded-sm text-[10px]
                                     bg-amber-500/10 border border-amber-500/30 text-amber-400 align-middle">
                      {locale === 'de' ? 'von' : 'from'} {actorLabel}
                    </span>
                  )}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

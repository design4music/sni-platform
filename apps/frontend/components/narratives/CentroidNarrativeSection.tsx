import { getNarrativesForCentroid, getNarrativeSparklines, getAllMetaNarratives } from '@/lib/queries';
import { getTranslations } from 'next-intl/server';
import NarrativeCard from './NarrativeCard';

interface Props {
  centroidId: string;
  locale: string;
}

export default async function CentroidNarrativeSection({ centroidId, locale }: Props) {
  const t = await getTranslations('narratives');
  const [narratives, sparklines, metaNarratives] = await Promise.all([
    getNarrativesForCentroid(centroidId, locale),
    getNarrativeSparklines(),
    getAllMetaNarratives(locale),
  ]);

  // Group by meta-narrative (may be empty)
  const metaMap = new Map(metaNarratives.map(m => [m.id, m.name]));
  const grouped = new Map<string, typeof narratives>();
  for (const n of narratives) {
    const key = n.meta_narrative_id;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(n);
  }

  return (
    <section>
      <h2 className="text-2xl font-bold mb-4">{t('strategicNarratives')}</h2>
      {narratives.length === 0 ? (
        <p className="text-sm text-dashboard-text-muted italic">
          {locale === 'de'
            ? 'Für dieses Land sind noch keine strategischen Narrative zugeordnet.'
            : 'No strategic narratives linked to this country yet.'}
        </p>
      ) : (
      <div className="space-y-6">
        {Array.from(grouped.entries()).map(([metaId, group]) => (
          <div key={metaId}>
            <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
              {metaMap.get(metaId) || metaId}
            </h3>
            <div className="space-y-1">
              {group.map(n => (
                <NarrativeCard
                  key={n.id}
                  id={n.id}
                  name={n.name}
                  actorCentroid={n.actor_centroid}
                  actorLabel={n.actor_label || null}
                  eventCount={n.event_count || 0}
                  sparkline={sparklines[n.id]}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      )}
    </section>
  );
}

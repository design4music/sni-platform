import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import NarrativeCard from '@/components/narratives/NarrativeCard';
import NarrativeFilterBar from '@/components/narratives/NarrativeFilterBar';
import { getAllMetaNarratives, getStrategicNarratives, getNarrativeSparklines } from '@/lib/queries';
import { buildAlternates } from '@/lib/seo';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import { getCentroidLabel } from '@/lib/types';
import Link from 'next/link';

export const revalidate = 21600;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('narratives');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: buildAlternates('/narratives'),
  };
}

interface Props {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ actor?: string; meta?: string; q?: string }>;
}

export default async function NarrativesPage({ params, searchParams }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narratives');
  const tCentroids = await getTranslations('centroids');
  const sp = await searchParams;

  const [metaNarratives, allNarratives, sparklines] = await Promise.all([
    getAllMetaNarratives(locale),
    getStrategicNarratives(locale),
    getNarrativeSparklines(),
  ]);

  // Build unique actors list for filter (with translated labels)
  const actorMap = new Map<string, string>();
  for (const n of allNarratives) {
    if (n.actor_centroid && n.actor_label) {
      actorMap.set(n.actor_centroid, getCentroidLabel(n.actor_centroid, n.actor_label, tCentroids));
    }
  }
  const actors = Array.from(actorMap.entries())
    .map(([id, label]) => ({ id, label }))
    .sort((a, b) => a.label.localeCompare(b.label));

  // Apply filters
  let filtered = allNarratives;
  if (sp.actor) {
    filtered = filtered.filter(n => n.actor_centroid === sp.actor);
  }
  if (sp.meta) {
    filtered = filtered.filter(n => n.meta_narrative_id === sp.meta);
  }
  if (sp.q) {
    const q = sp.q.toLowerCase();
    filtered = filtered.filter(n =>
      n.name.toLowerCase().includes(q) ||
      (n.claim && n.claim.toLowerCase().includes(q))
    );
  }

  // Group by meta-narrative
  const grouped = new Map<string, typeof filtered>();
  for (const n of filtered) {
    const key = n.meta_narrative_id;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(n);
  }

  return (
    <DashboardLayout>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold mb-1">{t('title')}</h1>
          <p className="text-dashboard-text-muted">{t('subtitle')}</p>
        </div>
        <Link
          href="/narratives/map"
          className="shrink-0 px-4 py-2 rounded-lg text-sm text-white bg-emerald-600 hover:bg-emerald-500 transition"
        >
          {t('mapView')}
        </Link>
      </div>

      <NarrativeFilterBar
        actors={actors}
        metaNarratives={metaNarratives.map(m => ({ id: m.id, name: m.name }))}
      />

      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-dashboard-text-muted text-lg">{t('noResults')}</p>
        </div>
      ) : (
        <div className="space-y-8">
          {metaNarratives.map(meta => {
            const narratives = grouped.get(meta.id);
            if (!narratives || narratives.length === 0) return null;
            return (
              <section key={meta.id}>
                <div className="flex items-center gap-3 mb-3">
                  <Link
                    href={`/narratives/meta/${meta.id}`}
                    className="text-xl font-bold text-dashboard-text hover:text-blue-400 transition"
                  >
                    {meta.name}
                  </Link>
                  <span className="text-xs text-dashboard-text-muted">
                    {narratives.length}
                  </span>
                </div>
                {meta.description && (
                  <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl">
                    {meta.description}
                  </p>
                )}
                <div className="space-y-1">
                  {narratives.map(n => (
                    <NarrativeCard
                      key={n.id}
                      id={n.id}
                      name={n.name}
                      actorCentroid={n.actor_centroid}
                      actorLabel={n.actor_label || null}
                      eventCount={n.event_count || 0}
                      sparkline={sparklines[n.id]}
                      matchedEventsLabel={t('matchedEvents')}
                      tCentroids={tCentroids}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </DashboardLayout>
  );
}

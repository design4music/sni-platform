import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import PositionCard from '@/components/narratives/PositionCard';
import FrictionNodesBrowser from '@/components/FrictionNodesBrowser';
import { getPositionsLanding } from '@/lib/queries';
import { getAllFrictionNodesByRegion } from '@/lib/friction-nodes';
import { buildAlternates } from '@/lib/seo';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import Link from 'next/link';

// Backed by mv_positions_landing (sub-ms PK lookup); no page-level HTML cache.
export const dynamic = 'force-dynamic';

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
}

export default async function NarrativesPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narratives');

  const [landing, fnByRegion] = await Promise.all([
    getPositionsLanding(locale),
    getAllFrictionNodesByRegion(locale),
  ]);

  const positions = landing?.positions ?? [];
  const metas = landing?.meta_narratives ?? [];
  const sparklines = landing?.sparklines ?? {};

  // Group positions by meta-narrative, largest reach first within a meta.
  const grouped = new Map<string, typeof positions>();
  for (const p of positions) {
    const arr = grouped.get(p.meta_narrative_id) ?? [];
    arr.push(p);
    grouped.set(p.meta_narrative_id, arr);
  }
  for (const arr of grouped.values()) {
    arr.sort((a, b) => b.event_count - a.event_count || a.name.localeCompare(b.name));
  }

  const cardLabels = { events: t('events'), owner: t('owner'), nodes: t('positionsLabel') };

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-1">{t('title')}</h1>
        <p className="text-dashboard-text-muted">{t('subtitle')}</p>
        <p className="mt-2 text-sm text-dashboard-text-muted">
          {positions.length} {t('positionsLabel')}
        </p>
      </div>

      {/* Friction Nodes Browser */}
      <div className="mb-10 rounded-lg border border-amber-700/40 bg-amber-950/20 p-6">
        <div className="mb-6 flex items-center gap-2">
          <span className="rounded bg-amber-600/30 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-200">
            Experimental
          </span>
          <span className="text-sm text-dashboard-text-muted">
            Friction Nodes — contested phenomena with pro/con narrative split
          </span>
        </div>
        <FrictionNodesBrowser data={fnByRegion} locale={locale} />
      </div>

      {positions.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-dashboard-text-muted text-lg">{t('noPositions')}</p>
        </div>
      ) : (
        <div className="space-y-8">
          {metas.map(meta => {
            const group = grouped.get(meta.id);
            if (!group || group.length === 0) return null;
            return (
              <section key={meta.id}>
                <div className="flex items-center gap-3 mb-3">
                  <Link
                    href={`/narratives/meta/${meta.id}`}
                    className="text-xl font-bold text-dashboard-text hover:text-blue-400 transition"
                  >
                    {meta.name}
                  </Link>
                  <span className="text-xs text-dashboard-text-muted">{group.length}</span>
                </div>
                {meta.description && (
                  <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl">
                    {meta.description}
                  </p>
                )}
                <div className="space-y-1">
                  {group.map(p => (
                    <PositionCard
                      key={p.id}
                      position={p}
                      sparkline={sparklines[p.id]}
                      labels={cardLabels}
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

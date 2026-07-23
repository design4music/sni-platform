import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import PositionCard from '@/components/narratives/PositionCard';
import MentionTimeline from '@/components/signals/MentionTimeline';
import { getPositionsLanding } from '@/lib/queries';
import { buildAlternates } from '@/lib/seo';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import type { SignalWeekly } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id, locale } = await params;
  const landing = await getPositionsLanding(locale);
  const meta = landing?.meta_narratives.find(m => m.id === id);
  if (!meta) return { title: 'Not Found' };
  return {
    title: meta.name,
    description: meta.description,
    alternates: buildAlternates(`/narratives/meta/${id}`),
  };
}

export default async function MetaNarrativePage({ params }: Props) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narratives');

  const landing = await getPositionsLanding(locale);
  const meta = landing?.meta_narratives.find(m => m.id === id);
  if (!meta) return notFound();

  const allMeta = landing?.meta_narratives ?? [];
  const sparklines = landing?.sparklines ?? {};
  const children = (landing?.positions ?? [])
    .filter(p => p.meta_narrative_id === id)
    .sort((a, b) => b.event_count - a.event_count || a.name.localeCompare(b.name));
  const totalEvents = children.reduce((s, p) => s + p.event_count, 0);

  // Aggregate the meta's timeline from its positions' weekly sparklines.
  const byWeek = new Map<string, number>();
  for (const p of children) {
    for (const w of sparklines[p.id] ?? []) {
      byWeek.set(w.week, (byWeek.get(w.week) ?? 0) + w.count);
    }
  }
  const weekly: SignalWeekly[] = Array.from(byWeek.entries())
    .map(([week, count]) => ({ week, count }))
    .sort((a, b) => a.week.localeCompare(b.week));

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      <Link href="/narratives" className="text-blue-400 hover:text-blue-300">{t('title')}</Link>
      <span className="mx-2">/</span>
      <span>{meta.name}</span>
    </div>
  );

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6">
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">{t('allMeta')}</h3>
        <nav className="space-y-1">
          {allMeta.map(m => (
            <Link
              key={m.id}
              href={`/narratives/meta/${m.id}`}
              className={`block px-3 py-2 rounded text-sm transition ${
                m.id === id
                  ? 'bg-blue-500/20 text-blue-400 font-medium'
                  : 'text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border'
              }`}
            >
              {m.name}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );

  const cardLabels = { events: t('events'), owner: t('owner'), nodes: t('positionsLabel') };

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">{meta.name}</h1>
        <p className="text-lg text-dashboard-text-muted mb-4">{meta.description}</p>
        <div className="flex items-center gap-4 text-sm text-dashboard-text-muted">
          <span>{children.length} {t('positionsLabel')}</span>
          <span>{totalEvents} {t('events').toLowerCase()}</span>
        </div>
      </div>

      {weekly.length > 0 && (
        <div className="mb-8"><MentionTimeline weekly={weekly} /></div>
      )}

      {children.length === 0 ? (
        <p className="text-dashboard-text-muted">{t('noPositions')}</p>
      ) : (
        <div className="space-y-1">
          {children.map(p => (
            <PositionCard key={p.id} position={p} sparkline={sparklines[p.id]} labels={cardLabels} />
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { setRequestLocale, getLocale } from 'next-intl/server';
import {
  getFrictionNodeView,
  getFrictionNodeWeeklyActivity,
} from '@/lib/friction-nodes';
import FrictionNodeNarrativeBricks from '@/components/friction-nodes/FrictionNodeNarrativeBricks';
import FrictionNodeNarrativeCards from '@/components/friction-nodes/FrictionNodeNarrativeCards';
import FrictionNodeActivityChart from '@/components/friction-nodes/FrictionNodeActivityChart';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, locale } = await params;
  const view = await getFrictionNodeView(slug, locale);
  if (!view) return { title: 'Not Found' };
  return {
    title: `${view.fn.name} — Friction Node | WorldBrief`,
    description: view.fn.description ?? view.fn.name,
    robots: { index: false, follow: false }, // shadow route
  };
}

export default async function FrictionNodePage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const intlLocale = await getLocale();

  const [view, weekly] = await Promise.all([
    getFrictionNodeView(slug, locale),
    getFrictionNodeWeeklyActivity(slug),
  ]);
  if (!view) return notFound();

  const isDe = intlLocale === 'de';

  // Locale-aware label bundles (kept inline since the shadow route doesn't
  // own its own messages namespace yet).
  const brickLabels = {
    sectionTitle: isDe ? 'Konkurrierende Narrative' : 'Competing narratives',
    sectionDescription: isDe
      ? 'Jede Karte unten ist eine Koalition mit ihrem eigenen Rahmen fuer dasselbe umstrittene Phaenomen. Klicken zum Springen zu Details.'
      : 'Each card below is one coalition with its own frame on the same contested phenomenon. Click to jump to detail.',
    titles: isDe ? 'Schlagzeilen' : 'titles',
    typeAllIn: isDe ? 'voll engagiert' : 'all in',
    typeStandBy: isDe ? 'allgemein' : 'stand by',
  };
  const cardLabels = {
    sectionTitle: isDe ? 'Narrative im Detail' : 'Narratives in detail',
    sectionDescription: isDe
      ? 'Geladenes Vokabular pro Koalition + juengste Schlagzeilen unter jedem Rahmen. Dieselbe Realitaet, unvereinbare Lesarten.'
      : 'Loaded vocabulary per coalition + recent headlines under each frame. The same reality, incompatible readings.',
    titles: brickLabels.titles,
    coalition: isDe ? 'Koalition' : 'Coalition',
    loadedVocabulary: isDe ? 'Geladenes Vokabular' : 'Loaded vocabulary',
    headlinesUnderFrame: isDe ? 'Schlagzeilen unter diesem Rahmen' : 'Headlines under this frame',
    noSamples: isDe ? 'noch keine Beispiele' : 'no samples yet',
    typeAllIn: brickLabels.typeAllIn,
    typeStandBy: brickLabels.typeStandBy,
    tier: isDe ? 'Ebene' : 'tier',
    claim: isDe ? 'Vollstaendige Behauptung' : 'Full claim',
  };
  const chartLabels = {
    sectionTitle: isDe ? 'Aktivitaet ueber die Zeit' : 'Activity over time',
    sectionDescription: isDe
      ? 'Woechentliche Schlagzeilenzahl pro Narrativ. Visuelle Asymmetrie ist Signal: einige Koalitionen dominieren das Vokabular, andere bleiben sporadisch.'
      : 'Weekly headline count per narrative. Visual asymmetry is signal: some coalitions dominate the vocabulary, others stay sporadic.',
    titles: brickLabels.titles,
    noData: isDe ? 'Noch keine Aktivitaetsdaten.' : 'No activity data yet.',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Shadow-route notice */}
      <div className="mb-6 px-3 py-2 rounded border border-amber-500/30 bg-amber-500/5 text-xs text-amber-400">
        {isDe
          ? 'Schatten-Route — experimentelle Friction-Node-Architektur. Noch nicht in der Hauptnavigation.'
          : 'Shadow route — experimental friction-node architecture. Not yet in main navigation.'}
      </div>

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-dashboard-text-muted mb-3">
        <Link href="/" className="text-blue-400 hover:text-blue-300">
          WorldBrief
        </Link>
        <span className="mx-2">/</span>
        <span>Friction Nodes</span>
        <span className="mx-2">/</span>
        <span>{view.fn.name}</span>
      </nav>

      {/* Header */}
      <header className="mb-8 pb-6 border-b border-dashboard-border">
        <div className="flex flex-wrap items-baseline gap-3 mb-3">
          <h1 className="text-3xl md:text-4xl font-bold text-dashboard-text">
            {view.fn.name}
          </h1>
          <span className="text-xs text-dashboard-text-muted font-mono">
            {view.fn.id}
          </span>
        </div>
        {view.fn.description && (
          <p className="text-base text-dashboard-text-muted leading-relaxed max-w-4xl">
            {view.fn.description}
          </p>
        )}
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-dashboard-text-muted">
          <div>
            <span className="uppercase tracking-wider mr-1">
              {isDe ? 'Schauplaetze' : 'Manifests in'}:
            </span>
            <span className="font-mono">{view.fn.centroid_ids.join(', ')}</span>
          </div>
          <div>
            <span className="uppercase tracking-wider mr-1">
              {isDe ? 'Narrative' : 'Narratives'}:
            </span>
            <span>{view.narratives.length}</span>
          </div>
          <div>
            <span className="uppercase tracking-wider mr-1">
              {isDe ? 'Verknuepfte Ereignisse' : 'Linked events'}:
            </span>
            <span>{view.event_count}</span>
          </div>
        </div>
        {view.fn.topic_keywords && view.fn.topic_keywords.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {view.fn.topic_keywords.map((kw) => (
              <span
                key={kw}
                className="text-[11px] text-dashboard-text-muted bg-dashboard-surface border border-dashboard-border px-2 py-0.5 rounded"
              >
                {kw}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* 1. Brick row — colour-coded narrative pills */}
      <FrictionNodeNarrativeBricks
        narratives={view.narratives}
        locale={intlLocale}
        labels={brickLabels}
      />

      {/* 2. Activity chart — stacked weekly area, all-time scale */}
      <FrictionNodeActivityChart
        narratives={view.narratives}
        weekly={weekly}
        labels={chartLabels}
      />

      {/* 3. Detailed narrative cards — 2-col grid with full vocabulary + headlines */}
      <FrictionNodeNarrativeCards
        narratives={view.narratives}
        locale={intlLocale}
        labels={cardLabels}
      />

      {/* Footer note */}
      <footer className="mt-12 pt-6 border-t border-dashboard-border text-xs text-dashboard-text-muted">
        {isDe
          ? 'Die Verknuepfung zwischen Schlagzeilen und Narrativen erfolgt derzeit ueber einen mechanischen Schluesselwortabgleich (topic UND framing muessen treffen). Die Pipeline-Integration ist noch nicht aktiv.'
          : 'Title-to-narrative attribution is currently via mechanical keyword match (topic AND framing must both hit). Pipeline integration not yet active.'}
      </footer>
    </div>
  );
}

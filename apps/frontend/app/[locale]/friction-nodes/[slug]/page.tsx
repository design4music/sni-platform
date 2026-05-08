import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { setRequestLocale, getLocale } from 'next-intl/server';
import DashboardLayout from '@/components/DashboardLayout';
import JsonLd from '@/components/JsonLd';
import { buildPageMetadata, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import {
  getFrictionNodeView,
  getFrictionNodeWeeklyActivity,
  getFrictionNodeEventsByWeek,
  getRelatedFrictionNodes,
  getCentroidLookup,
  getTheaterForAtomicFn,
  getTheaterMembers,
  getFrictionNodeBySlug,
} from '@/lib/friction-nodes';
import type { CentroidLookupEntry } from '@/lib/friction-nodes-shared';
import FrictionNodeNarrativeBricks from '@/components/friction-nodes/FrictionNodeNarrativeBricks';
import FrictionNodeNarrativeCards from '@/components/friction-nodes/FrictionNodeNarrativeCards';
import FrictionNodeActivityChart from '@/components/friction-nodes/FrictionNodeActivityChart';
import FrictionNodeEventsByWeek from '@/components/friction-nodes/FrictionNodeEventsByWeek';
import FrictionNodeRelated from '@/components/friction-nodes/FrictionNodeRelated';
import CoalitionPills from '@/components/friction-nodes/CoalitionPills';
import FrictionNodeTheaterMember from '@/components/friction-nodes/FrictionNodeTheaterMember';

// Shadow route. Force-dynamic + lib/cache.ts query memoization (per
// project convention — see lib/cache.ts and the ISR-cache-sizing memory).
export const dynamic = 'force-dynamic';

// SHADOW: noindex while not in main navigation. Flip to remove the
// robots override (and remove the in-page amber notice) when ready
// to promote.
const IS_SHADOW = true;

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, locale } = await params;
  const view = await getFrictionNodeView(slug, locale);
  if (!view) return { title: 'Not Found' };
  const meta = buildPageMetadata({
    title: `${view.fn.name} | Friction Node`,
    description: view.fn.editorial_summary ?? view.fn.description ?? view.fn.name,
    path: `/friction-nodes/${slug}`,
    locale: locale as SeoLocale,
    ogType: 'article',
  });
  if (IS_SHADOW) meta.robots = { index: false, follow: false };
  return meta;
}

export default async function FrictionNodePage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const intlLocale = await getLocale();

  // Branch by fn_type: theater rows render a different (lighter) layout.
  // Cheap pre-fetch — getFrictionNodeBySlug is cached and gets re-used by
  // getFrictionNodeView below for atomic FNs.
  const fnRow = await getFrictionNodeBySlug(slug, locale);
  if (!fnRow) return notFound();
  if (fnRow.fn_type === 'theater') {
    return renderTheaterPage(slug, fnRow, intlLocale);
  }

  const [view, weekly, weeklyEvents, related, theater] = await Promise.all([
    getFrictionNodeView(slug, locale),
    getFrictionNodeWeeklyActivity(slug),
    getFrictionNodeEventsByWeek(slug, locale, 10),
    getRelatedFrictionNodes(slug, locale),
    getTheaterForAtomicFn(slug, locale),
  ]);
  if (!view) return notFound();

  // Resolve all centroid IDs touched by the FN or its narratives so we can
  // render country pills (flag + label) instead of raw IDs.
  const allCentroidIds = new Set<string>(view.fn.centroid_ids);
  for (const n of view.narratives) for (const c of n.actor_centroids) allCentroidIds.add(c);
  const centroidEntries = await getCentroidLookup(Array.from(allCentroidIds));
  const centroidLookup = new Map<string, CentroidLookupEntry>(
    centroidEntries.map((e) => [e.id, e]),
  );

  const isDe = intlLocale === 'de';
  const totalAttributed = view.narratives.reduce((acc, n) => acc + n.match_count, 0);

  // Locale-aware label bundles.
  const brickLabels = {
    sectionTitle: isDe ? 'Konkurrierende Narrative' : 'Competing narratives',
    sectionDescription: isDe
      ? 'Jede Karte unten ist eine Koalition mit ihrem eigenen Rahmen fuer dasselbe umstrittene Phaenomen.'
      : 'Each card below is one coalition with its own frame on the same contested phenomenon.',
    titles: isDe ? 'Schlagzeilen' : 'titles',
    typeAllIn: isDe ? 'voll engagiert' : 'all in',
    typeStandBy: isDe ? 'allgemein' : 'stand by',
  };
  const cardLabels = {
    sectionTitle: isDe ? 'Narrative im Detail' : 'Narratives in detail',
    sectionDescription: isDe
      ? 'Geladenes Vokabular pro Koalition und juengste Schlagzeilen unter jedem Rahmen.'
      : 'Loaded vocabulary per coalition and recent headlines under each frame.',
    titles: brickLabels.titles,
    coalition: isDe ? 'Koalition' : 'Coalition',
    loadedVocabulary: isDe ? 'Geladenes Vokabular' : 'Loaded vocabulary',
    headlinesUnderFrame: isDe ? 'Schlagzeilen unter diesem Rahmen' : 'Headlines under this frame',
    noSamples: isDe ? 'noch keine Beispiele' : 'no samples yet',
    claim: isDe ? 'Vollstaendige Behauptung' : 'Full claim',
    coveredBy: isDe ? 'Gedeckt von' : 'Covered by',
  };
  const chartLabels = {
    sectionTitle: isDe ? 'Narrativ-Verteilung ueber die Zeit' : 'Narrative distribution over time',
    sectionDescription: isDe
      ? 'Woechentliche Anzahl zugeordneter Schlagzeilen pro Narrativ. Visuelle Asymmetrie ist Signal: einige Koalitionen dominieren das Vokabular, andere bleiben sporadisch.'
      : 'Weekly attributed-headline count per narrative. Visual asymmetry is signal: some coalitions dominate the vocabulary, others stay sporadic.',
    titles: brickLabels.titles,
    noData: isDe ? 'Noch keine Aktivitaetsdaten.' : 'No activity data yet.',
  };
  const eventsLabels = {
    sectionTitle: isDe ? 'Ereignisse pro Woche' : 'Events per week',
    sectionDescription: isDe
      ? 'Wochenweise Verteilung der Ereignisse auf dieser Friction Node. Klick auf einen Balken zeigt die Top-Ereignisse dieser Woche.'
      : 'Per-week distribution of events on this friction node. Click a bar to see that week\'s top events.',
    chartHelpText: isDe
      ? 'Klick auf einen Wochenbalken zur Auswahl. Hellblau = aktive Woche.'
      : 'Click a week bar to select. Light blue = active week.',
    weekOf: isDe ? 'Woche vom' : 'Week of',
    eventsThisWeek: isDe ? 'Ereignisse' : 'events',
    moreThisWeek: isDe ? '+{n} weitere diese Woche' : '+{n} more this week',
    sources: isDe ? 'Quellen' : 'sources',
    importance: isDe ? 'Bedeutung' : 'importance',
    none: isDe ? 'keine Ereignisse' : 'no events',
    selectAWeek: isDe ? '(Top-Ereignisse aller Wochen)' : '(top events across all weeks)',
    showAll: isDe ? 'Alle Wochen' : 'All weeks',
  };
  const relatedLabels = {
    sectionTitle: isDe ? 'Verwandte Friction Nodes' : 'Related friction nodes',
    sectionDescription: isDe
      ? 'Andere Friction Nodes, die mindestens zwei Narrative mit dieser teilen.'
      : 'Other friction nodes sharing at least two narratives with this one.',
    sharedNarratives: isDe ? 'gemeinsame Narrative' : 'shared narratives',
    none: isDe
      ? 'Noch keine verwandten Friction Nodes; weitere Friction Nodes muessen hinzugefuegt werden.'
      : 'No related friction nodes yet. More friction nodes need to be added.',
  };

  // BreadcrumbList JSON-LD for SEO.
  const breadcrumbJson = breadcrumbList([
    { name: 'WorldBrief', path: '/' },
    { name: isDe ? 'Friction Nodes' : 'Friction Nodes', path: '/friction-nodes' },
    { name: view.fn.name, path: `/friction-nodes/${slug}` },
  ]);

  return (
    <DashboardLayout>
      <JsonLd data={breadcrumbJson} />

      {IS_SHADOW && (
        <div className="mb-6 px-3 py-2 rounded border border-amber-500/30 bg-amber-500/5 text-xs text-amber-400">
          {isDe
            ? 'Schatten-Route. Experimentelle Friction-Node-Architektur, noch nicht in der Hauptnavigation.'
            : 'Shadow route. Experimental friction-node architecture, not yet in main navigation.'}
        </div>
      )}

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

      {/* HEADER (2-column) */}
      <header className="mb-8 pb-6 border-b border-dashboard-border grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        {/* LEFT 2/3 — title, editorial summary, counts */}
        <div className="lg:col-span-2 min-w-0">
          {theater && (
            <div className="mb-3">
              <Link
                href={`/${intlLocale}/friction-nodes/${theater.id}`}
                className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-amber-400 hover:text-amber-300 bg-amber-500/5 border border-amber-500/30 px-2.5 py-1 rounded transition"
              >
                <span>{isDe ? 'Teil von' : 'Part of'}:</span>
                <span className="font-semibold normal-case tracking-normal">{theater.name}</span>
                <span aria-hidden>&rarr;</span>
              </Link>
            </div>
          )}
          <div className="flex flex-wrap items-baseline gap-3 mb-3">
            <h1 className="text-3xl md:text-4xl font-bold text-dashboard-text">
              {view.fn.name}
            </h1>
            <span className="text-xs text-dashboard-text-muted font-mono">
              {view.fn.id}
            </span>
          </div>

          {view.fn.editorial_summary && (
            <p className="text-base text-dashboard-text leading-relaxed mb-4">
              {view.fn.editorial_summary}
            </p>
          )}

          {/* Counts strip */}
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-dashboard-text-muted">
            <div>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Konkurrierende Narrative' : 'Competing narratives'}:
              </span>
              <span className="text-dashboard-text">{view.narratives.length}</span>
            </div>
            <div title={isDe ? 'Promotete Ereignisse, die das Phaenomen dieser FN beruehren' : 'Promoted events that touch this FN\'s phenomenon'}>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Ereignisse' : 'Events'}:
              </span>
              <span className="text-dashboard-text">{view.event_count}</span>
            </div>
            <div title={isDe ? 'Schlagzeilen, die einer Narrativ-Koalition zugeordnet sind' : 'Headlines bucketed into a narrative coalition'}>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Zugeordnete Schlagzeilen' : 'Attributed headlines'}:
              </span>
              <span className="text-dashboard-text">{totalAttributed}</span>
            </div>
          </div>
        </div>

        {/* RIGHT 1/3 — sidebar with countries + topic tags + what-is-contested */}
        <aside className="space-y-5 min-w-0">
          {/* Manifests in (countries) */}
          {view.fn.centroid_ids.length > 0 && (
            <div>
              <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
                {isDe ? 'Schauplaetze' : 'Manifests in'}
              </div>
              <CoalitionPills centroidIds={view.fn.centroid_ids} lookup={centroidLookup} />
            </div>
          )}

          {/* Topic tags */}
          {view.fn.topic_keywords && view.fn.topic_keywords.length > 0 && (
            <div>
              <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
                {isDe ? 'Themenmarker' : 'Topic markers'}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {view.fn.topic_keywords.slice(0, 14).map((kw) => (
                  <span
                    key={kw}
                    className="text-[11px] text-dashboard-text-muted bg-dashboard-bg border border-dashboard-border/60 px-2 py-0.5 rounded"
                  >
                    {kw}
                  </span>
                ))}
                {view.fn.topic_keywords.length > 14 && (
                  <span className="text-[11px] text-dashboard-text-muted">
                    +{view.fn.topic_keywords.length - 14}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* What is contested (description) — collapsed by default */}
          {view.fn.description && (
            <details className="group">
              <summary className="text-[11px] uppercase tracking-wider text-dashboard-text-muted cursor-pointer hover:text-dashboard-text transition select-none">
                {isDe ? 'Was ist umstritten' : 'What is contested'}
              </summary>
              <p className="mt-2 text-sm text-dashboard-text-muted leading-relaxed">
                {view.fn.description}
              </p>
            </details>
          )}
        </aside>
      </header>

      {/* 1. Brick row */}
      <FrictionNodeNarrativeBricks
        narratives={view.narratives}
        locale={intlLocale}
        labels={brickLabels}
      />

      {/* 2. Narrative distribution chart (interpretive layer only) */}
      <section className="mb-10">
        <FrictionNodeActivityChart
          narratives={view.narratives}
          weekly={weekly}
          labels={chartLabels}
        />
      </section>

      {/* 3. Detailed narrative cards */}
      <FrictionNodeNarrativeCards
        narratives={view.narratives}
        centroidLookup={centroidLookup}
        locale={intlLocale}
        labels={cardLabels}
      />

      {/* 4. Events per week — clickable bars + per-week list */}
      <FrictionNodeEventsByWeek weeks={weeklyEvents} labels={eventsLabels} />

      {/* 5. Related friction nodes */}
      <FrictionNodeRelated related={related} locale={intlLocale} labels={relatedLabels} />

      {/* Methodology note */}
      <div className="mt-12 pt-6 border-t border-dashboard-border text-xs text-dashboard-text-muted">
        {isDe
          ? 'Die Verknuepfung zwischen Schlagzeilen und Narrativen erfolgt derzeit ueber Publisher-Stance-Bucketing plus FN-Themenabgleich. Pipeline-Integration noch nicht aktiv.'
          : 'Title-to-narrative attribution currently uses publisher-stance bucketing plus FN topic match. Pipeline integration not yet active.'}
      </div>
    </DashboardLayout>
  );
}

// ----------------------------------------------------------------------
// Theater landing page (fn_type === 'theater').
// Lighter than the atomic FN page: no narrative bricks/cards/charts — a
// theater itself doesn't have narratives or events directly. Instead we
// list the constituent atomic FNs with a stance-brick preview underneath
// each, so visitors can drill into the specific contested phenomenon.
// ----------------------------------------------------------------------
async function renderTheaterPage(
  slug: string,
  fn: Awaited<ReturnType<typeof getFrictionNodeBySlug>> & object,
  intlLocale: string,
) {
  const isDe = intlLocale === 'de';
  const [members, centroidEntries] = await Promise.all([
    getTheaterMembers(slug, intlLocale),
    getCentroidLookup(fn.centroid_ids ?? []),
  ]);
  const centroidLookup = new Map<string, CentroidLookupEntry>(
    centroidEntries.map((e) => [e.id, e]),
  );

  const breadcrumbJson = breadcrumbList([
    { name: 'WorldBrief', path: '/' },
    { name: 'Friction Nodes', path: '/friction-nodes' },
    { name: fn.name, path: `/friction-nodes/${slug}` },
  ]);

  const totalEvents = members.reduce((acc, m) => acc + m.event_count, 0);
  const totalAttributed = members.reduce(
    (acc, m) => acc + m.stances.reduce((a, s) => a + s.match_count, 0),
    0,
  );

  return (
    <DashboardLayout>
      <JsonLd data={breadcrumbJson} />

      {IS_SHADOW && (
        <div className="mb-6 px-3 py-2 rounded border border-amber-500/30 bg-amber-500/5 text-xs text-amber-400">
          {isDe
            ? 'Schatten-Route. Experimentelle Friction-Node-Architektur, noch nicht in der Hauptnavigation.'
            : 'Shadow route. Experimental friction-node architecture, not yet in main navigation.'}
        </div>
      )}

      <nav aria-label="Breadcrumb" className="text-sm text-dashboard-text-muted mb-3">
        <Link href="/" className="text-blue-400 hover:text-blue-300">
          WorldBrief
        </Link>
        <span className="mx-2">/</span>
        <span>Friction Nodes</span>
        <span className="mx-2">/</span>
        <span>{fn.name}</span>
      </nav>

      <header className="mb-8 pb-6 border-b border-dashboard-border grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        <div className="lg:col-span-2 min-w-0">
          <div className="mb-3">
            <span className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-violet-400 bg-violet-500/5 border border-violet-500/30 px-2.5 py-1 rounded">
              {isDe ? 'Theater' : 'Theater'}
            </span>
          </div>
          <div className="flex flex-wrap items-baseline gap-3 mb-3">
            <h1 className="text-3xl md:text-4xl font-bold text-dashboard-text">{fn.name}</h1>
            <span className="text-xs text-dashboard-text-muted font-mono">{fn.id}</span>
          </div>
          {fn.editorial_summary && (
            <p className="text-base text-dashboard-text leading-relaxed mb-4">
              {fn.editorial_summary}
            </p>
          )}
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-dashboard-text-muted">
            <div>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Atomare Friction Nodes' : 'Atomic friction nodes'}:
              </span>
              <span className="text-dashboard-text">{members.length}</span>
            </div>
            <div>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Ereignisse gesamt' : 'Events (combined)'}:
              </span>
              <span className="text-dashboard-text">{totalEvents}</span>
            </div>
            <div>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Zugeordnete Schlagzeilen' : 'Attributed headlines'}:
              </span>
              <span className="text-dashboard-text">{totalAttributed}</span>
            </div>
          </div>
        </div>
        <aside className="space-y-5 min-w-0">
          {fn.centroid_ids.length > 0 && (
            <div>
              <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
                {isDe ? 'Schauplaetze' : 'Manifests in'}
              </div>
              <CoalitionPills centroidIds={fn.centroid_ids} lookup={centroidLookup} />
            </div>
          )}
          {fn.description && (
            <details className="group">
              <summary className="text-[11px] uppercase tracking-wider text-dashboard-text-muted cursor-pointer hover:text-dashboard-text transition select-none">
                {isDe ? 'Was bindet diese FNs zusammen' : 'What ties these FNs together'}
              </summary>
              <p className="mt-2 text-sm text-dashboard-text-muted leading-relaxed">
                {fn.description}
              </p>
            </details>
          )}
        </aside>
      </header>

      <section className="mb-10">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-dashboard-text mb-1">
            {isDe ? 'Atomare Friction Nodes in diesem Theater' : 'Atomic friction nodes in this theater'}
          </h2>
          <p className="text-sm text-dashboard-text-muted">
            {isDe
              ? 'Jeder ist ein eigenstaendiges umstrittenes Phaenomen mit eigenen Koalitionen. Klick auf eine Karte zur Detailansicht.'
              : 'Each is a distinct contested phenomenon with its own coalitions. Click any card to drill in.'}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {members.map((m) => (
            <FrictionNodeTheaterMember
              key={m.id}
              member={m}
              locale={intlLocale}
              isDe={isDe}
            />
          ))}
        </div>
        {!members.length && (
          <div className="text-sm text-dashboard-text-muted">
            {isDe
              ? 'Noch keine atomaren Friction Nodes diesem Theater zugeordnet.'
              : 'No atomic friction nodes assigned to this theater yet.'}
          </div>
        )}
      </section>
    </DashboardLayout>
  );
}

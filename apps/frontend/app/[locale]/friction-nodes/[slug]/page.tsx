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
  getCentroidLookup,
  getTheaterForAtomicFn,
  getTheaterMembers,
  getFrictionNodeBySlug,
} from '@/lib/friction-nodes';
import type { CentroidLookupEntry } from '@/lib/friction-nodes-shared';
import { filterNarrativesForDisplay } from '@/lib/friction-nodes-shared';
import FrictionNodeNarrativeBricks from '@/components/friction-nodes/FrictionNodeNarrativeBricks';
import FrictionNodeNarrativeCards from '@/components/friction-nodes/FrictionNodeNarrativeCards';
import FrictionNodeActivityChart from '@/components/friction-nodes/FrictionNodeActivityChart';
import FrictionNodeEventsByWeek from '@/components/friction-nodes/FrictionNodeEventsByWeek';
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
    title: `${view.fn.name} | Conflict`,
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

  const [view, weekly, weeklyEvents, theater] = await Promise.all([
    getFrictionNodeView(slug, locale),
    getFrictionNodeWeeklyActivity(slug),
    getFrictionNodeEventsByWeek(slug, locale, 10),
    getTheaterForAtomicFn(slug, locale),
  ]);
  if (!view) return notFound();

  // "Specific conflicts in this zone" -- same section as the theater
  // landing page, reused here so a reader sees the full sibling set (incl.
  // itself, muted) rather than a plain link list. Depends on theater's id,
  // so it can't join the Promise.all above.
  const theaterMembers = theater ? await getTheaterMembers(theater.id, locale) : [];

  // Resolve all centroid IDs touched by the FN or its narratives so we can
  // render country pills (flag + label) instead of raw IDs.
  const allCentroidIds = new Set<string>(view.fn.centroid_ids);
  for (const n of view.narratives) for (const c of n.actor_centroids) allCentroidIds.add(c);
  const centroidEntries = await getCentroidLookup(Array.from(allCentroidIds));
  const centroidLookup = new Map<string, CentroidLookupEntry>(
    centroidEntries.map((e) => [e.id, e]),
  );

  const isDe = intlLocale === 'de';
  // Attributed-headline total stays the true aggregate (includes titles on
  // any hidden thin narrative below); the narrative-count stat below uses
  // displayNarratives so it matches the cards actually rendered.
  const totalAttributed = view.narratives.reduce((acc, n) => acc + n.match_count, 0);
  const displayNarratives = filterNarrativesForDisplay(view.narratives);

  // Locale-aware label bundles.
  const brickLabels = {
    sectionTitle: isDe ? 'Konkurrierende Narrative' : 'Competing narratives',
    sectionDescription: isDe
      ? 'Jede Karte unten ist eine Koalition mit ihrem eigenen Rahmen fuer dasselbe umstrittene Phaenomen.'
      : 'Each card below is one coalition with its own frame on the same contested phenomenon.',
    titles: isDe ? 'Schlagzeilen' : 'titles',
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
      ? 'Wochenweise Verteilung der Ereignisse zu diesem Konflikt. Klick auf einen Balken zeigt die Top-Ereignisse dieser Woche.'
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
  // BreadcrumbList JSON-LD for SEO.
  const breadcrumbJson = breadcrumbList([
    { name: 'WorldBrief', path: '/' },
    { name: isDe ? 'Konflikte' : 'Conflicts', path: '/friction-nodes' },
    { name: view.fn.name, path: `/friction-nodes/${slug}` },
  ]);

  return (
    <DashboardLayout>
      <JsonLd data={breadcrumbJson} />

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-dashboard-text-muted mb-3">
        <Link href="/" className="text-blue-400 hover:text-blue-300">
          WorldBrief
        </Link>
        <span className="mx-2">/</span>
        <span>{isDe ? 'Konflikte' : 'Conflicts'}</span>
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
          <h1 className="text-3xl md:text-4xl font-bold text-dashboard-text mb-3">
            {view.fn.name}
          </h1>

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
              <span className="text-dashboard-text">{displayNarratives.length}</span>
            </div>
            <div title={isDe ? 'Schlagzeilen, die einer Narrativ-Koalition zugeordnet sind' : 'Headlines bucketed into a narrative coalition'}>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Zugeordnete Schlagzeilen' : 'Attributed headlines'}:
              </span>
              <span className="text-dashboard-text">{totalAttributed}</span>
            </div>
          </div>
        </div>

        {/* RIGHT 1/3 — sidebar with topic tags + what-is-contested.
            "Manifests in" removed 2026-05-11: friction_nodes.centroid_ids
            now stores the narrow actor-scope for attribution, not the
            broader "all involved parties" set. Coverage by country is
            implicit in the narratives' actor_centroids. */}
        <aside className="space-y-5 min-w-0">
          {/* Topic markers section removed 2026-05-12: friction_nodes.topic_keywords
              dropped. Vocab now lives in taxonomy_v3 fn_anchor bundle. */}

          {/* What is contested — always visible */}
          {view.fn.description && (
            <div>
              <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
                {isDe ? 'Was ist umstritten' : 'What is contested'}
              </div>
              <p className="text-sm text-dashboard-text-muted leading-relaxed">
                {view.fn.description}
              </p>
            </div>
          )}
        </aside>
      </header>

      {/* 1. Brick row -- first two narratives always shown; a thin 3rd+
           nuance narrative stays hidden until it crosses 5 attributed
           titles (see filterNarrativesForDisplay). */}
      <FrictionNodeNarrativeBricks
        narratives={displayNarratives}
        locale={intlLocale}
        labels={brickLabels}
      />

      {/* 2. Narrative distribution chart (interpretive layer only) */}
      <section className="mb-10">
        <FrictionNodeActivityChart
          narratives={displayNarratives}
          weekly={weekly}
          labels={chartLabels}
        />
      </section>

      {/* 3. Detailed narrative cards */}
      <FrictionNodeNarrativeCards
        narratives={displayNarratives}
        centroidLookup={centroidLookup}
        locale={intlLocale}
        labels={cardLabels}
      />

      {/* 4. Events per week — clickable bars + per-week list */}
      <FrictionNodeEventsByWeek weeks={weeklyEvents} labels={eventsLabels} />

      {/* 5. Specific conflicts in this zone -- same section as the theater
           landing page; the current FN's own card renders muted/inert. */}
      {theaterMembers.length > 0 && (
        <section className="mb-10">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-dashboard-text mb-1">
              {isDe ? 'Spezifische Konflikte in dieser Zone' : 'Specific conflicts in this zone'}
            </h2>
            <p className="text-sm text-dashboard-text-muted">
              {isDe
                ? 'Eigenstaendige Konflikte mit eigenen Koalitionen. Schlagzeilen, die hierher gehoeren, erscheinen nicht oben.'
                : 'Distinct conflicts with their own coalitions. Headlines that fit here do not show in the umbrella above.'}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {theaterMembers.map((m) => (
              <FrictionNodeTheaterMember
                key={m.id}
                member={m}
                locale={intlLocale}
                isDe={isDe}
                isCurrent={m.id === slug}
              />
            ))}
          </div>
        </section>
      )}

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
  // Theater is the umbrella catch-all FN. fn_type='theater' carries both
  // the navigation grouping (member_fn_ids) AND catch-all attribution
  // semantics. It hosts the broad-cluster narratives (war coalitions,
  // diplomatic/multipolar bridges).
  const [members, view] = await Promise.all([
    getTheaterMembers(slug, intlLocale),
    getFrictionNodeView(slug, intlLocale),
  ]);
  const theaterNarratives = view?.narratives ?? [];
  // Card/brick display only -- first two theater narratives always shown;
  // a thin 3rd+ nuance narrative hides until it crosses 5 attributed titles.
  const displayTheaterNarratives = filterNarrativesForDisplay(theaterNarratives);
  // Resolve every centroid touched by the theater itself or by any of its
  // narratives, so narrative-card country pills find their flag/label.
  const allCentroidIds = new Set<string>(fn.centroid_ids ?? []);
  for (const n of theaterNarratives) {
    for (const c of n.actor_centroids) allCentroidIds.add(c);
  }
  const centroidEntries = await getCentroidLookup(Array.from(allCentroidIds));
  const centroidLookup = new Map<string, CentroidLookupEntry>(
    centroidEntries.map((e) => [e.id, e]),
  );

  const breadcrumbJson = breadcrumbList([
    { name: 'WorldBrief', path: '/' },
    { name: 'Conflicts', path: '/friction-nodes' },
    { name: fn.name, path: `/friction-nodes/${slug}` },
  ]);

  const totalAttributed = members.reduce(
    (acc, m) => acc + m.stances.reduce((a, s) => a + s.match_count, 0),
    0,
  );

  return (
    <DashboardLayout>
      <JsonLd data={breadcrumbJson} />

      <nav aria-label="Breadcrumb" className="text-sm text-dashboard-text-muted mb-3">
        <Link href="/" className="text-blue-400 hover:text-blue-300">
          WorldBrief
        </Link>
        <span className="mx-2">/</span>
        <span>{isDe ? 'Konflikte' : 'Conflicts'}</span>
        <span className="mx-2">/</span>
        <span>{fn.name}</span>
      </nav>

      <header className="mb-8 pb-6 border-b border-dashboard-border grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        <div className="lg:col-span-2 min-w-0">
          <div className="mb-3">
            <span className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-violet-400 bg-violet-500/5 border border-violet-500/30 px-2.5 py-1 rounded">
              {isDe ? 'Konfliktzone' : 'Conflict zone'}
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-dashboard-text mb-3">{fn.name}</h1>
          {fn.editorial_summary && (
            <p className="text-base text-dashboard-text leading-relaxed mb-4">
              {fn.editorial_summary}
            </p>
          )}
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-dashboard-text-muted">
            <div>
              <span className="uppercase tracking-wider mr-1">
                {isDe ? 'Konflikte in dieser Zone' : 'Conflicts in this zone'}:
              </span>
              <span className="text-dashboard-text">{members.length}</span>
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
          {fn.description && (
            <div>
              <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
                {isDe ? 'Was diese Konflikte verbindet' : 'What ties these conflicts together'}
              </div>
              <p className="text-sm text-dashboard-text-muted leading-relaxed">
                {fn.description}
              </p>
            </div>
          )}
        </aside>
      </header>

      {/* Theater narratives — umbrella coalitions (war + diplomatic bridges) */}
      {theaterNarratives.length > 0 && (
        <>
          <FrictionNodeNarrativeBricks
            narratives={displayTheaterNarratives}
            locale={intlLocale}
            labels={{
              sectionTitle: isDe ? 'Konkurrierende Narrative' : 'Competing narratives',
              sectionDescription: isDe
                ? 'Koalitionen mit eigenen Rahmen fuer den uebergreifenden Konflikt.'
                : 'Coalitions with their own frame on the umbrella conflict.',
              titles: isDe ? 'Schlagzeilen' : 'titles',
            }}
          />
          <FrictionNodeNarrativeCards
            narratives={displayTheaterNarratives}
            centroidLookup={centroidLookup}
            locale={intlLocale}
            labels={{
              sectionTitle: isDe ? 'Narrative im Detail' : 'Narratives in detail',
              sectionDescription: isDe
                ? 'Geladenes Vokabular pro Koalition und juengste Schlagzeilen.'
                : 'Loaded vocabulary per coalition and recent headlines.',
              titles: isDe ? 'Schlagzeilen' : 'titles',
              coalition: isDe ? 'Koalition' : 'Coalition',
              loadedVocabulary: isDe ? 'Geladenes Vokabular' : 'Loaded vocabulary',
              headlinesUnderFrame: isDe ? 'Schlagzeilen unter diesem Rahmen' : 'Headlines under this frame',
              noSamples: isDe ? 'noch keine Beispiele' : 'no samples yet',
              claim: isDe ? 'Vollstaendige Behauptung' : 'Full claim',
              coveredBy: isDe ? 'Gedeckt von' : 'Covered by',
            }}
          />
        </>
      )}

      <section className="mb-10">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-dashboard-text mb-1">
            {isDe ? 'Spezifische Konflikte in dieser Zone' : 'Specific conflicts in this zone'}
          </h2>
          <p className="text-sm text-dashboard-text-muted">
            {isDe
              ? 'Eigenstaendige Konflikte mit eigenen Koalitionen. Schlagzeilen, die hierher gehoeren, erscheinen nicht oben.'
              : 'Distinct conflicts with their own coalitions. Headlines that fit here do not show in the umbrella above.'}
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
              ? 'Noch keine Konflikte dieser Zone zugeordnet.'
              : 'No conflicts assigned to this zone yet.'}
          </div>
        )}
      </section>
    </DashboardLayout>
  );
}

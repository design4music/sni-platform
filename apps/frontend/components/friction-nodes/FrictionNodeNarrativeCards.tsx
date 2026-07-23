import Link from 'next/link';
import type { NarrativeOnFn, SampleTitle, CentroidLookupEntry } from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';
import CoalitionPills from './CoalitionPills';

interface Props {
  narratives: NarrativeOnFn[];
  centroidLookup: Map<string, CentroidLookupEntry>;
  locale: string;
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    titles: string;
    coalition: string;
    loadedVocabulary: string;
    headlinesUnderFrame: string;
    noSamples: string;
    claim: string;
    coveredBy: string;
  };
}

function formatDate(dateStr: string, locale: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function NarrativeCard({
  n,
  centroidLookup,
  locale,
  labels,
}: {
  n: NarrativeOnFn;
  centroidLookup: Map<string, CentroidLookupEntry>;
  locale: string;
  labels: Props['labels'];
}) {
  const hue = colorForNarrative(n.stance);
  const anchorId = `narrative-${n.narrative_id}`;
  const isDe = locale === 'de';

  return (
    <article
      id={anchorId}
      className="p-6 border border-dashboard-border bg-dashboard-surface rounded-lg scroll-mt-20 relative"
    >
      {/* Coloured accent bar */}
      <div
        aria-hidden
        className="absolute top-0 left-0 right-0 h-1 rounded-t-lg"
        style={{ backgroundColor: hue, opacity: 0.85 }}
      />

      {/* Header: stance label + count */}
      <header className="flex items-start gap-3 mb-2 flex-wrap pt-1">
        <h3 className="text-xl font-bold leading-tight text-dashboard-text flex-1 min-w-0">
          <span
            aria-hidden
            className="inline-block w-2.5 h-2.5 rounded-sm mr-2 align-middle"
            style={{ backgroundColor: hue }}
          />
          {n.stance_label}
        </h3>
        <span
          className="inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium bg-dashboard-border/50 border-dashboard-border text-dashboard-text-muted tabular-nums shrink-0"
          title={`${n.match_count} ${labels.titles}`}
        >
          {n.match_count} {labels.titles}
        </span>
      </header>

      {/* Up-link to the parent position (SPEC v2) -- full position title so the
          connection is obvious at a glance */}
      {n.position_id && (
        <Link
          href={`/narratives/${n.position_id}`}
          title={n.position_name ?? undefined}
          className="block mb-4 text-xs text-blue-400 hover:text-blue-300 transition"
        >
          <span className="uppercase tracking-wider text-dashboard-text-muted mr-1">
            {isDe ? 'Position' : 'View position'}:
          </span>
          <span className="leading-snug">{n.position_name ?? (isDe ? 'ansehen' : 'view')}</span>
          {' '}&rarr;
        </Link>
      )}

      {/* Loaded vocabulary */}
      {n.framing_keywords && n.framing_keywords.length > 0 && (
        <div className="mb-4">
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
            {labels.loadedVocabulary}
          </div>
          <div className="flex flex-wrap gap-1">
            {n.framing_keywords.slice(0, 8).map((kw) => (
              <span
                key={kw}
                className="text-[11px] italic text-dashboard-text bg-dashboard-bg border border-dashboard-border/60 px-1.5 py-0.5 rounded"
              >
                &ldquo;{kw}&rdquo;
              </span>
            ))}
            {n.framing_keywords.length > 8 && (
              <span className="text-[11px] text-dashboard-text-muted">
                +{n.framing_keywords.length - 8}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Full claim — always visible; it is core content, not a disclosure */}
      {n.narrative_claim && (
        <p className="mb-4 text-sm text-dashboard-text leading-relaxed">
          {n.narrative_claim}
        </p>
      )}

      {/* Coalition + covered-by, grouped as the editorial basis */}
      <div className="mb-4">
        <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
          {labels.coalition}
        </div>
        <CoalitionPills centroidIds={n.actor_centroids} lookup={centroidLookup} />
        {n.publishers && n.publishers.length > 0 && (
          <div className="mt-2 text-[11px] text-dashboard-text-muted leading-snug">
            <span className="uppercase tracking-wider mr-1">{labels.coveredBy}:</span>
            <span>
              {n.publishers.slice(0, 6).join(' · ')}
              {n.publishers.length > 6 && (
                <span className="opacity-70"> · +{n.publishers.length - 6}</span>
              )}
            </span>
          </div>
        )}
      </div>

      {/* Recent headlines */}
      <div>
        <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
          {labels.headlinesUnderFrame}
        </div>
        {n.sample_titles.length === 0 ? (
          <div className="text-xs text-dashboard-text-muted italic">{labels.noSamples}</div>
        ) : (
          <ul className="space-y-1.5">
            {n.sample_titles.map((t: SampleTitle) => (
              <li key={t.id} className="text-sm leading-snug">
                <span className="text-dashboard-text">{t.title}</span>
                <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-dashboard-text-muted">
                  <span className="truncate">{t.publisher_name ?? '—'}</span>
                  <span className="font-mono shrink-0">{formatDate(t.pubdate_utc, locale)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}

export default function FrictionNodeNarrativeCards({ narratives, centroidLookup, locale, labels }: Props) {
  if (narratives.length === 0) return null;
  const isDe = locale === 'de';

  // Two stacked columns by stance sign (SPEC v2 §5.3): supporting / critical,
  // neutral in its own band below.
  const supporting = narratives.filter((n) => (n.stance ?? 0) > 0);
  const critical = narratives.filter((n) => (n.stance ?? 0) < 0);
  const neutral = narratives.filter((n) => (n.stance ?? 0) === 0);

  const col = (n: NarrativeOnFn) => (
    <NarrativeCard key={n.narrative_id} n={n} centroidLookup={centroidLookup} locale={locale} labels={labels} />
  );
  const heading = (text: string, color: string, count: number) => (
    <h3 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${color}`}>{text} · {count}</h3>
  );

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        <div className="space-y-4">
          {heading(isDe ? 'Zustimmend' : 'Supporting', 'text-emerald-400/80', supporting.length)}
          {supporting.map(col)}
        </div>
        <div className="space-y-4">
          {heading(isDe ? 'Kritisch' : 'Critical', 'text-rose-400/80', critical.length)}
          {critical.map(col)}
        </div>
      </div>
      {neutral.length > 0 && (
        <div className="mt-4">
          {heading(isDe ? 'Neutral' : 'Neutral', 'text-slate-400/80', neutral.length)}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">{neutral.map(col)}</div>
        </div>
      )}
    </section>
  );
}

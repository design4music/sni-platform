import type { NarrativeOnFn, SampleTitle } from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';

interface Props {
  narratives: NarrativeOnFn[];
  locale: string;
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    titles: string;
    coalition: string;
    loadedVocabulary: string;
    headlinesUnderFrame: string;
    noSamples: string;
    typeAllIn: string;
    typeStandBy: string;
    tier: string;
    claim: string;
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
  locale,
  labels,
}: {
  n: NarrativeOnFn;
  locale: string;
  labels: Props['labels'];
}) {
  const hue = colorForNarrative(n.display_order);
  const typeLabel = n.narrative_type === 'all_in' ? labels.typeAllIn : labels.typeStandBy;
  const anchorId = `narrative-${n.narrative_id}`;

  return (
    <article
      id={anchorId}
      className="p-6 border border-dashboard-border bg-dashboard-surface rounded-lg scroll-mt-20 relative"
    >
      {/* Coloured accent bar — top of the card matches the brick colour */}
      <div
        aria-hidden
        className="absolute top-0 left-0 right-0 h-1 rounded-t-lg"
        style={{ backgroundColor: hue, opacity: 0.85 }}
      />

      {/* Header: stance label + count badge */}
      <header className="flex items-start gap-3 mb-3 flex-wrap pt-1">
        <h3
          className="text-xl font-bold leading-tight text-dashboard-text flex-1 min-w-0"
        >
          <span
            aria-hidden
            className="inline-block w-2.5 h-2.5 rounded-sm mr-2 align-middle"
            style={{ backgroundColor: hue }}
          />
          {n.stance_label}
        </h3>
        <span
          className="ml-auto inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium bg-dashboard-border/50 border-dashboard-border text-dashboard-text-muted tabular-nums shrink-0"
          title={`${n.match_count} ${labels.titles}`}
        >
          {n.match_count} {labels.titles}
        </span>
      </header>

      {/* Type + tier pills */}
      <div className="flex flex-wrap items-center gap-1.5 mb-4">
        <span
          className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border"
          style={{
            backgroundColor: hue + '22',
            color: hue,
            borderColor: hue + '55',
          }}
        >
          {typeLabel}
        </span>
        {n.tier && (
          <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border bg-purple-500/10 text-purple-400 border-purple-500/30">
            {n.tier}
          </span>
        )}
        <span className="text-[10px] font-mono text-dashboard-text-muted">
          {n.narrative_id}
        </span>
      </div>

      {/* Coalition (centroid IDs) */}
      <div className="mb-4">
        <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
          {labels.coalition}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {n.actor_centroids.map((c) => (
            <span
              key={c}
              className="inline-flex items-center px-2 py-0.5 rounded-full border border-dashboard-border bg-dashboard-border/30 text-xs font-mono text-dashboard-text"
            >
              {c}
            </span>
          ))}
        </div>
      </div>

      {/* Loaded vocabulary */}
      {n.framing_keywords && n.framing_keywords.length > 0 && (
        <div className="mb-4">
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
            {labels.loadedVocabulary}
          </div>
          <div className="flex flex-wrap gap-1">
            {n.framing_keywords.slice(0, 12).map((kw) => (
              <span
                key={kw}
                className="text-[11px] italic text-dashboard-text bg-dashboard-bg border border-dashboard-border/60 px-1.5 py-0.5 rounded"
              >
                &ldquo;{kw}&rdquo;
              </span>
            ))}
            {n.framing_keywords.length > 12 && (
              <span className="text-[11px] text-dashboard-text-muted">
                +{n.framing_keywords.length - 12}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Claim text — collapsed to 2 lines via line-clamp; full text on hover via title attr */}
      {n.narrative_claim && (
        <details className="mb-4 group">
          <summary className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5 cursor-pointer select-none hover:text-dashboard-text transition">
            {labels.claim}
          </summary>
          <p className="text-sm text-dashboard-text-muted leading-relaxed mt-2 max-h-64 overflow-y-auto pr-1">
            {n.narrative_claim}
          </p>
        </details>
      )}

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

/**
 * 2-column grid of detailed narrative cards on a friction-node page.
 * Mirrors the layout convention of OutletStanceSection cards.
 */
export default function FrictionNodeNarrativeCards({ narratives, locale, labels }: Props) {
  if (narratives.length === 0) return null;
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {narratives.map((n) => (
          <NarrativeCard key={n.narrative_id} n={n} locale={locale} labels={labels} />
        ))}
      </div>
    </section>
  );
}

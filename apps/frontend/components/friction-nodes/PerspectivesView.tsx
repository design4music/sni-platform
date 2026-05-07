import Link from 'next/link';
import type { NarrativeOnFn, SampleTitle } from '@/lib/friction-nodes-shared';

interface Props {
  narratives: NarrativeOnFn[];
  locale: string;
}

function formatDate(dateStr: string, locale: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function NarrativeColumn({ n, locale }: { n: NarrativeOnFn; locale: string }) {
  const typeBadge = n.narrative_type === 'all_in'
    ? { label: locale === 'de' ? 'voll engagiert' : 'all in', cls: 'bg-blue-500/15 text-blue-400 border-blue-500/30' }
    : { label: locale === 'de' ? 'allgemein' : 'stand by', cls: 'bg-slate-500/15 text-slate-400 border-slate-500/30' };

  return (
    <div className="flex flex-col w-full md:w-[280px] md:shrink-0 bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
      {/* Stance label header */}
      <div className="mb-2">
        <h3 className="text-base font-semibold text-dashboard-text leading-snug">
          {n.stance_label}
        </h3>
        <div className="mt-1 flex flex-wrap items-center gap-1.5">
          <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${typeBadge.cls}`}>
            {typeBadge.label}
          </span>
          {n.tier && (
            <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border bg-purple-500/10 text-purple-400 border-purple-500/30">
              {n.tier}
            </span>
          )}
        </div>
      </div>

      {/* Coalition */}
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-wider text-dashboard-text-muted mb-1">
          {locale === 'de' ? 'Koalition' : 'Coalition'}
        </div>
        <div className="flex flex-wrap gap-1">
          {n.actor_centroids.map((c) => (
            <span key={c} className="text-[11px] font-mono text-dashboard-text-muted bg-dashboard-bg px-1.5 py-0.5 rounded">
              {c}
            </span>
          ))}
        </div>
      </div>

      {/* Framing keywords */}
      {n.framing_keywords && n.framing_keywords.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] uppercase tracking-wider text-dashboard-text-muted mb-1">
            {locale === 'de' ? 'Vokabular' : 'Loaded vocabulary'}
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

      {/* Recent headlines feeding this frame */}
      <div className="mt-2">
        <div className="text-[10px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
          {locale === 'de' ? 'Schlagzeilen unter diesem Rahmen' : 'Headlines under this frame'}
        </div>
        {n.sample_titles.length === 0 ? (
          <div className="text-xs text-dashboard-text-muted italic">
            {locale === 'de' ? 'noch keine Beispiele' : 'no samples yet'}
          </div>
        ) : (
          <ul className="space-y-1.5">
            {n.sample_titles.map((t: SampleTitle) => (
              <li key={t.id} className="text-xs leading-snug">
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
    </div>
  );
}

export default function PerspectivesView({ narratives, locale }: Props) {
  if (narratives.length === 0) {
    return (
      <div className="text-sm text-dashboard-text-muted italic">
        {locale === 'de' ? 'keine Narrative verknüpft' : 'no narratives linked yet'}
      </div>
    );
  }

  return (
    <div className="-mx-4 px-4 md:mx-0 md:px-0">
      <div className="flex flex-col md:flex-row gap-4 md:overflow-x-auto md:pb-4 md:snap-x">
        {narratives.map((n) => (
          <div key={n.narrative_id} className="md:snap-start">
            <NarrativeColumn n={n} locale={locale} />
          </div>
        ))}
      </div>
    </div>
  );
}

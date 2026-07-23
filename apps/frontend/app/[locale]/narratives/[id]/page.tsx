import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import MentionTimeline from '@/components/signals/MentionTimeline';
import { getPositionById } from '@/lib/queries';
import { buildPageMetadata, articleJsonLd, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import type { PositionCardRow } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id, locale } = await params;
  const detail = await getPositionById(id, locale);
  if (!detail) return { title: 'Not Found' };
  const p = detail.position;
  return buildPageMetadata({
    title: p.name,
    description: p.claim || p.name,
    path: `/narratives/${id}`,
    locale: locale as SeoLocale,
    ogType: 'article',
  });
}

function formatDate(dateStr: string, locale: string = 'en-US'): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function stanceDot(sign: number): string {
  if (sign > 0) return 'bg-emerald-500';
  if (sign < 0) return 'bg-rose-500';
  return 'bg-slate-500';
}

function cardTone(stance: number): string {
  if (stance > 0) return 'border-l-emerald-500/60';
  if (stance < 0) return 'border-l-rose-500/60';
  return 'border-l-slate-500/60';
}

export default async function PositionDetailPage({ params }: Props) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narratives');
  const intlLocale = await getLocale();

  const detail = await getPositionById(id, locale);
  if (!detail) return notFound();
  const p = detail.position;

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted flex flex-wrap items-baseline gap-y-0.5 overflow-hidden">
      <Link href="/narratives" className="text-blue-400 hover:text-blue-300 shrink-0">{t('title')}</Link>
      <span className="mx-1 md:mx-2 shrink-0">/</span>
      {p.meta_name && (
        <>
          <Link href={`/narratives/meta/${p.meta_narrative_id}`} className="text-blue-400 hover:text-blue-300">{p.meta_name}</Link>
          <span className="mx-1 md:mx-2 shrink-0">/</span>
        </>
      )}
      <span>{p.name}</span>
    </div>
  );

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6">
      {/* Meta card */}
      {p.meta_name && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('meta')}</h3>
          <Link href={`/narratives/meta/${p.meta_narrative_id}`} className="text-base font-medium text-blue-400 hover:text-blue-300 transition">
            {p.meta_name}
          </Link>
          {p.meta_secondary.length > 0 && (
            <p className="mt-2 text-xs text-dashboard-text-muted">
              {t('secondaryMeta')}: {p.meta_secondary.map(m => m.name).join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Owner / coalition card */}
      {(p.owner_centroids.length > 0 || p.coalitions.length > 0) && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('owner')}</h3>
          <div className="flex flex-wrap gap-1.5">
            {p.owner_centroids.map(o => (
              <Link key={o.id} href={`/c/${o.id}`} className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 hover:bg-blue-500/20 transition">
                {o.label}
              </Link>
            ))}
          </div>
          {p.coalitions.length > 0 && (
            <>
              <h3 className="mt-4 text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('coalition')}</h3>
              <div className="flex flex-wrap gap-1.5">
                {p.coalitions.map(c => (
                  <span key={c.coalition} className="text-xs px-2 py-0.5 rounded-full bg-dashboard-border/60 font-mono text-dashboard-text-muted" title={`${c.cards} ${t('appearsOn').toLowerCase()}`}>
                    {c.coalition}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Cross-node reach */}
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('crossNodeReach')}</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-dashboard-text">{p.fn_count}</span>
          <span className="text-xs text-dashboard-text-muted">{t('positionsLabel')} · {p.event_count} {t('events').toLowerCase()}</span>
        </div>
      </div>

      {/* Sibling positions (competing) */}
      {detail.siblings.length > 0 && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">{t('competingPositions')}</h3>
          <div className="space-y-2">
            {detail.siblings.map(s => (
              <Link key={s.id} href={`/narratives/${s.id}`} className="flex items-start gap-2 group">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${stanceDot(s.stance_sign)}`} />
                <span className="text-sm text-dashboard-text-muted group-hover:text-blue-400 transition">
                  {s.name}
                  <span className="ml-1 text-[10px] opacity-60">· {s.shared_fns} {t('sharedNodes')}</span>
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const jsonLd = [
    articleJsonLd({ headline: p.name, description: p.claim || p.name, path: `/narratives/${p.id}`, locale: locale as SeoLocale }),
    breadcrumbList([
      { name: 'Narratives', path: '/narratives' },
      { name: p.name, path: `/narratives/${p.id}` },
    ]),
  ];

  const renderCard = (c: PositionCardRow) => (
    <Link
      key={c.id}
      href={`/friction-nodes/${c.fn_id}`}
      className={`flex flex-col gap-1 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border border-l-2 ${cardTone(c.stance)} hover:border-blue-500/40 transition`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm font-medium text-dashboard-text">{c.fn_name}</span>
        <span className="text-xs text-dashboard-text-muted tabular-nums shrink-0" title={t('headlines')}>{c.match_count}</span>
      </div>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-dashboard-text-muted">
        {c.stance_label && <span>{c.stance_label}</span>}
        {c.coalition && <span className="rounded bg-dashboard-border/60 px-1.5 py-0.5 font-mono text-[10px]">{c.coalition}</span>}
        <span className="opacity-60">{c.publisher_count} pub.</span>
      </div>
    </Link>
  );

  const supporting = detail.cards.filter(c => c.stance > 0);
  const critical = detail.cards.filter(c => c.stance < 0);
  const neutral = detail.cards.filter(c => c.stance === 0);

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      <JsonLd data={jsonLd} />
      {/* Header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <div className="flex items-start gap-3 mb-4">
          <span className={`mt-2 h-3 w-3 shrink-0 rounded-full ${stanceDot(p.stance_sign)}`} />
          <h1 className="text-3xl md:text-4xl font-bold">{p.name}</h1>
        </div>
        {p.claim && (
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-1">{t('claim')}</h2>
            <p className="text-lg text-dashboard-text">{p.claim}</p>
          </div>
        )}
        {p.normative_line && (
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-1">{t('normativeConclusion')}</h2>
            <p className="text-dashboard-text-muted">{p.normative_line}</p>
          </div>
        )}
        {p.keywords.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('keywords')}</h2>
            <div className="flex flex-wrap gap-1.5">
              {p.keywords.map((kw, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400">{kw}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      {detail.weekly_activity.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-dashboard-text-muted">{t('timeline')}</h2>
          <MentionTimeline weekly={detail.weekly_activity} />
        </div>
      )}

      {/* Where this position appears -- two columns */}
      {detail.cards.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-dashboard-text-muted">{t('appearsOn')}</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400/80">{t('supporting')} · {supporting.length}</h3>
              {supporting.map(renderCard)}
            </div>
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-rose-400/80">{t('critical')} · {critical.length}</h3>
              {critical.map(renderCard)}
            </div>
          </div>
          {neutral.length > 0 && (
            <div className="mt-4 space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400/80">{t('neutralBand')} · {neutral.length}</h3>
              <div className="grid gap-2 md:grid-cols-2">{neutral.map(renderCard)}</div>
            </div>
          )}
        </div>
      )}

      {/* Derived events */}
      {detail.events.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-dashboard-text-muted">{t('matchedEvents')}</h2>
          <div className="space-y-2">
            {detail.events.map(ev => (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
              >
                <span className="text-sm text-dashboard-text md:truncate md:flex-1">{ev.title}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-dashboard-text-muted font-mono shrink-0">{formatDate(ev.date, intlLocale)}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full shrink-0 bg-blue-500/20 text-blue-400" title={t('headlines')}>{ev.title_count}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

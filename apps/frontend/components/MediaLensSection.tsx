import Link from 'next/link';
import FlagImg from './FlagImg';
import type { CentroidMediaLensRow } from '@/lib/queries';

interface Props {
  rows: CentroidMediaLensRow[];
  centroidLabel: string;
  month: string; // YYYY-MM
  locale: string;
}

// Matches the OutletStanceHeatmap palette so colour reads consistently
// across the site.
function stanceHue(stance: number | null): string {
  if (stance == null) return '#71717a';
  if (stance <= -2) return '#b91c1c';
  if (stance === -1) return '#ef4444';
  if (stance === 0) return '#71717a';
  if (stance === 1) return '#10b981';
  return '#15803d';
}

function stanceLabel(stance: number | null, loc: string): string {
  if (stance == null) return loc === 'de' ? 'unklar' : 'unclear';
  if (loc === 'de') {
    if (stance <= -2) return 'sehr kritisch';
    if (stance === -1) return 'kritisch';
    if (stance === 0) return 'neutral';
    if (stance === 1) return 'unterstützend';
    return 'sehr unterstützend';
  }
  if (stance <= -2) return 'very critical';
  if (stance === -1) return 'critical';
  if (stance === 0) return 'neutral';
  if (stance === 1) return 'supportive';
  return 'very supportive';
}

export default function MediaLensSection({ rows, centroidLabel, month, locale }: Props) {
  if (rows.length === 0) return null;

  const heading = locale === 'de' ? 'Medienperspektive' : 'Media Lens';
  const sub = locale === 'de'
    ? `Top-Quellen über ${centroidLabel}`
    : `Top sources covering ${centroidLabel}`;

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
        {heading}
      </h3>
      <p className="text-[11px] text-dashboard-text-muted mb-3 -mt-2">{sub}</p>
      <ul className="space-y-2">
        {rows.map(r => {
          const href = r.outlet_slug
            ? `/${locale}/sources/${r.outlet_slug}/${month}`
            : null;
          const inner = (
            <div className="flex items-start gap-2.5">
              {r.country_code && (
                <FlagImg iso2={r.country_code} className="mt-0.5 shrink-0" />
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-sm font-medium text-dashboard-text">
                  <span className="truncate">{r.outlet_name}</span>
                  <span
                    className="shrink-0 inline-block w-2 h-2 rounded-full"
                    style={{ backgroundColor: stanceHue(r.stance) }}
                    title={stanceLabel(r.stance, locale)}
                  />
                </div>
                {r.tone && (
                  <p className="text-xs text-dashboard-text-muted leading-snug mt-0.5 line-clamp-2">
                    {r.tone}
                  </p>
                )}
              </div>
            </div>
          );
          return (
            <li key={r.outlet_name} className="rounded hover:bg-dashboard-border/30 transition px-2 py-1.5 -mx-2">
              {href ? (
                <Link href={href} className="block">{inner}</Link>
              ) : inner}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

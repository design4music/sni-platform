import { getTranslations } from 'next-intl/server';
import { getCountryName } from '@/lib/countries';
import PersonIcon from './PersonIcon';
import type { OutletStanceEntity } from '@/lib/queries';

interface Props {
  entities: OutletStanceEntity[];
}

/** Hue for the brick background. Same palette as the cross-month
 *  heatmap on the landing page so the visual stays coherent. */
function stanceHue(stance: number | null): string {
  if (stance == null) return '#71717a'; // zinc-500
  if (stance <= -2) return '#b91c1c';
  if (stance === -1) return '#ef4444';
  if (stance === 0) return '#71717a';
  if (stance === 1) return '#10b981';
  return '#15803d';
}

/** Background opacity scales with coverage volume so heavily-covered
 *  entities pop. Floor of 0.45 keeps colour readable. */
function brickOpacity(n: number, max: number): number {
  if (n <= 0 || max <= 0) return 0.45;
  const t = Math.log10(n + 1) / Math.log10(max + 1);
  return 0.45 + 0.5 * t;
}

function stanceText(stance: number | null): string {
  if (stance == null) return '?';
  return stance > 0 ? `+${stance}` : `${stance}`;
}

export default async function OutletStanceBricks({ entities }: Props) {
  const t = await getTranslations('sources');

  if (entities.length === 0) return null;

  let max = 0;
  for (const e of entities) if (e.n_headlines > max) max = e.n_headlines;
  if (max === 0) max = 1;

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{t('stanceBricksTitle')}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {t('stanceBricksDescription')}
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {entities.map(e => {
          const isPerson = e.entity_kind === 'person';
          const label = isPerson
            ? e.entity_code
            : getCountryName(e.entity_code) || e.entity_code;
          const hue = stanceHue(e.stance);
          const op = brickOpacity(e.n_headlines, max);
          const anchorId = `stance-${e.entity_kind}-${e.entity_code}`;
          return (
            <a
              key={`${e.entity_kind}-${e.entity_code}`}
              href={`#${anchorId}`}
              className="block rounded-lg p-3 transition hover:ring-2 hover:ring-blue-400/60 text-white relative overflow-hidden"
              style={{ backgroundColor: hue, opacity: op }}
              title={`${label} — ${e.n_headlines} ${t('titles')}`}
            >
              <div className="flex items-center gap-1.5 mb-1 min-w-0">
                {isPerson && (
                  <PersonIcon className="w-3.5 h-3.5 flex-shrink-0" />
                )}
                <span className="text-sm font-medium truncate">{label}</span>
              </div>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-3xl font-bold tabular-nums leading-none">
                  {stanceText(e.stance)}
                </span>
                <span className="text-[11px] tabular-nums opacity-90">
                  {e.n_headlines} {t('titles')}
                </span>
              </div>
            </a>
          );
        })}
      </div>
    </section>
  );
}

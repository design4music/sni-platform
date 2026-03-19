import Link from 'next/link';
import { getCompetingNarratives } from '@/lib/queries';
import { getTranslations } from 'next-intl/server';

interface Props {
  narrativeId: string;
  actorCentroid: string | null;
  locale: string;
}

export default async function CompetingNarrativesPanel({ narrativeId, locale }: Props) {
  const t = await getTranslations('narratives');
  const competing = await getCompetingNarratives(narrativeId);

  if (competing.length === 0) return null;

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
        {t('competing')}
      </h3>
      <div className="space-y-2">
        {competing.map(n => (
          <Link
            key={n.id}
            href={`/narratives/${n.id}`}
            className="block px-3 py-2 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border transition"
          >
            <p className="text-sm font-medium text-dashboard-text">{n.name}</p>
            <div className="flex items-center gap-2 mt-1">
              {n.actor_label && (
                <span className="text-xs text-dashboard-text-muted">{n.actor_label}</span>
              )}
              <span className="text-xs text-dashboard-text-muted">
                {n.shared_events} {t('sharedEvents')}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

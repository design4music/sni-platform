'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';

interface Props {
  actors: { id: string; label: string }[];
  metaNarratives: { id: string; name: string }[];
}

export default function NarrativeFilterBar({ actors, metaNarratives }: Props) {
  const t = useTranslations('narratives');
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const currentActor = searchParams.get('actor') || '';
  const currentMeta = searchParams.get('meta') || '';
  const currentSearch = searchParams.get('q') || '';

  function update(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="flex flex-wrap items-center gap-3 mb-6">
      <input
        type="text"
        defaultValue={currentSearch}
        placeholder={t('filter')}
        onChange={(e) => update('q', e.target.value)}
        className="px-3 py-2 bg-dashboard-surface border border-dashboard-border rounded-lg text-sm text-dashboard-text placeholder-dashboard-text-muted focus:outline-none focus:border-blue-500 w-64"
      />
      <select
        value={currentActor}
        onChange={(e) => update('actor', e.target.value)}
        className="px-3 py-2 bg-dashboard-surface border border-dashboard-border rounded-lg text-sm text-dashboard-text focus:outline-none focus:border-blue-500"
      >
        <option value="">{t('actor')}</option>
        {actors.map(a => (
          <option key={a.id} value={a.id}>{a.label}</option>
        ))}
      </select>
      <select
        value={currentMeta}
        onChange={(e) => update('meta', e.target.value)}
        className="px-3 py-2 bg-dashboard-surface border border-dashboard-border rounded-lg text-sm text-dashboard-text focus:outline-none focus:border-blue-500"
      >
        <option value="">{t('meta')}</option>
        {metaNarratives.map(m => (
          <option key={m.id} value={m.id}>{m.name}</option>
        ))}
      </select>
    </div>
  );
}

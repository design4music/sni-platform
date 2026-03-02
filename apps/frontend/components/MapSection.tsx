'use client';

import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';

const WorldMap = dynamic(() => import('./WorldMap'), { ssr: false });

interface MapSectionProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes?: string[];
  }>;
}

export default function MapSection({ centroids }: MapSectionProps) {
  const t = useTranslations('map');
  return (
    <section>
      <h2 className="text-3xl font-bold mb-4">{t('title')}</h2>
      <p className="text-dashboard-text-muted mb-6">
        {t('subtitle')}
      </p>
      <WorldMap centroids={centroids} />
    </section>
  );
}

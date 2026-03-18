import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import NarrativeMapView from '@/components/narratives/NarrativeMapView';
import { getNarrativeMapData, getCentroidIsoMap } from '@/lib/queries';
import { setRequestLocale, getTranslations } from 'next-intl/server';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('narrativeMap');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: { canonical: '/narratives/map' },
  };
}

interface Props {
  params: Promise<{ locale: string }>;
}

export default async function NarrativeMapPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narrativeMap');

  const [narratives, centroidIsoMap] = await Promise.all([
    getNarrativeMapData(locale),
    getCentroidIsoMap(),
  ]);

  return (
    <DashboardLayout>
      <div className="mb-4">
        <h1 className="text-3xl md:text-4xl font-bold mb-1">{t('title')}</h1>
        <p className="text-dashboard-text-muted">{t('subtitle')}</p>
      </div>
      <div className="h-[calc(100vh-12rem)]">
        <NarrativeMapView narratives={narratives} centroidIsoMap={centroidIsoMap} />
      </div>
    </DashboardLayout>
  );
}

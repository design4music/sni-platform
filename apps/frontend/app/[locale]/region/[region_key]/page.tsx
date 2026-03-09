import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import CentroidCard from '@/components/CentroidCard';
import { getCentroidsByTheater } from '@/lib/queries';
import { REGIONS, RegionKey } from '@/lib/types';
import { notFound } from 'next/navigation';
import { getTranslations, getLocale } from 'next-intl/server';

export const revalidate = 300;

interface RegionPageProps {
  params: Promise<{ region_key: string }>;
}

export async function generateMetadata({ params }: RegionPageProps): Promise<Metadata> {
  const t = await getTranslations('regions');
  const { region_key } = await params;
  const regionKey = region_key.toUpperCase() as RegionKey;
  const label = REGIONS[regionKey];
  if (!label) return { title: t('notFound') };
  return {
    title: label,
    description: t('metaDescription', { label }),
    alternates: { canonical: `/region/${region_key.toLowerCase()}` },
  };
}

export default async function RegionPage({ params }: RegionPageProps) {
  const t = await getTranslations('regions');
  const { region_key } = await params;

  const regionKey = region_key.toUpperCase() as RegionKey;
  const regionLabel = REGIONS[regionKey];

  if (!regionLabel) {
    notFound();
  }

  const locale = await getLocale();
  const centroids = await getCentroidsByTheater(regionKey, locale);

  return (
    <DashboardLayout title={regionLabel}>
      <div className="space-y-6">
        <p className="text-xl text-dashboard-text-muted">
          {t('subtitle')}
        </p>

        {centroids.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-dashboard-text-muted">{t('noCentroids')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {centroids.map(centroid => (
              <CentroidCard key={centroid.id} centroid={centroid} />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

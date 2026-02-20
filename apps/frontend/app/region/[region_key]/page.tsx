import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import CentroidCard from '@/components/CentroidCard';
import { getCentroidsByTheater } from '@/lib/queries';
import { REGIONS, RegionKey } from '@/lib/types';
import { notFound } from 'next/navigation';

export const revalidate = 300;

export function generateStaticParams() {
  return Object.keys(REGIONS).map(key => ({ region_key: key.toLowerCase() }));
}

interface RegionPageProps {
  params: Promise<{ region_key: string }>;
}

export async function generateMetadata({ params }: RegionPageProps): Promise<Metadata> {
  const { region_key } = await params;
  const regionKey = region_key.toUpperCase() as RegionKey;
  const label = REGIONS[regionKey];
  if (!label) return { title: 'Region Not Found' };
  return {
    title: label,
    description: `${label} news intelligence: countries and sub-regions covered by WorldBrief with multilingual source analysis and narrative tracking.`,
    alternates: { canonical: `/region/${region_key.toLowerCase()}` },
  };
}

export default async function RegionPage({ params }: RegionPageProps) {
  const { region_key } = await params;

  const regionKey = region_key.toUpperCase() as RegionKey;
  const regionLabel = REGIONS[regionKey];

  if (!regionLabel) {
    notFound();
  }

  const centroids = await getCentroidsByTheater(regionKey);

  return (
    <DashboardLayout title={regionLabel}>
      <div className="space-y-6">
        <p className="text-xl text-dashboard-text-muted">
          Countries and sub-regions covered in this area
        </p>

        {centroids.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-dashboard-text-muted">No centroids found in this region</p>
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

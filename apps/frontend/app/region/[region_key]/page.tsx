import DashboardLayout from '@/components/DashboardLayout';
import CentroidCard from '@/components/CentroidCard';
import { getCentroidsByTheater } from '@/lib/queries';
import { REGIONS, RegionKey } from '@/lib/types';
import { notFound } from 'next/navigation';

export const dynamic = 'force-dynamic';

interface RegionPageProps {
  params: Promise<{ region_key: string }>;
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

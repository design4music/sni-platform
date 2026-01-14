import DashboardLayout from '@/components/DashboardLayout';
import CentroidCard from '@/components/CentroidCard';
import { getCentroidsByClass } from '@/lib/queries';

export const dynamic = 'force-dynamic';

export default async function GlobalPage() {
  const systemicCentroids = await getCentroidsByClass('systemic');
  const geoCentroids = await getCentroidsByClass('geo');

  // Non-State Actors are geo centroids with IDs starting with "NON-STATE-"
  const nonStateActors = geoCentroids.filter(c => c.id.startsWith('NON-STATE-'));

  return (
    <DashboardLayout title="Global Centroids">
      <div className="space-y-12">
        <section>
          <h2 className="text-2xl font-bold mb-4">Systemic Lenses</h2>
          <p className="text-dashboard-text-muted mb-6">
            Global thematic perspectives on strategic developments
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {systemicCentroids.map(centroid => (
              <CentroidCard key={centroid.id} centroid={centroid} showClass />
            ))}
          </div>
        </section>

        {nonStateActors.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold mb-4">Non-State Actors</h2>
            <p className="text-dashboard-text-muted mb-6">
              International organizations and non-state entities
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {nonStateActors.map(centroid => (
                <CentroidCard key={centroid.id} centroid={centroid} showClass />
              ))}
            </div>
          </section>
        )}
      </div>
    </DashboardLayout>
  );
}

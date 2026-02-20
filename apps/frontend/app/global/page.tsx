import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import CentroidCard from '@/components/CentroidCard';
import { getCentroidsByClass } from '@/lib/queries';

export const revalidate = 300;

export const metadata: Metadata = {
  title: 'Global & Systemic',
  description: 'Systemic lenses and non-state actors: cross-border themes like trade, energy, climate, and technology tracked across global news coverage.',
  alternates: { canonical: '/global' },
};

export default async function GlobalPage() {
  const systemicCentroids = await getCentroidsByClass('systemic');
  const geoCentroids = await getCentroidsByClass('geo');

  // Non-State Actors are geo centroids with IDs starting with "NON-STATE-"
  const nonStateActors = geoCentroids.filter(c => c.id.startsWith('NON-STATE-'));

  return (
    <DashboardLayout title="Strategic Developments Worldwide">
      <div className="space-y-12">
        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6">
          <p className="text-yellow-200 font-medium">
            This section is a conceptual illustration and a work in progress.
            The mechanism for identifying and extracting major global developments
            across thematic areas is still in an active research phase.
            Content shown here may be incomplete, improperly grouped, or subject to change.
          </p>
        </div>
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

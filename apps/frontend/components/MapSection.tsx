'use client';

import dynamic from 'next/dynamic';

const WorldMap = dynamic(() => import('./WorldMap'), { ssr: false });

interface MapSectionProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes?: string[];
  }>;
}

export default function MapSection({ centroids }: MapSectionProps) {
  return (
    <section>
      <h2 className="text-3xl font-bold mb-6">Geographic Intelligence</h2>
      <p className="text-dashboard-text-muted mb-6">
        Click on any highlighted country or region to explore its strategic narrative
      </p>
      <WorldMap centroids={centroids} />
    </section>
  );
}

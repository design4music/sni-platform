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
      <h2 className="text-3xl font-bold mb-4">Explore the world by country</h2>
      <p className="text-dashboard-text-muted mb-6">
        Click on any highlighted country or region to see a structured overview of recent developments.
        Each page brings together the main topics covered in the news, grouped by domain and time period,
        with links to original sources.
      </p>
      <WorldMap centroids={centroids} />
    </section>
  );
}

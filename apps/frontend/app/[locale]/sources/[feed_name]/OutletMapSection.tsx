'use client';

import dynamic from 'next/dynamic';

const WorldMap = dynamic(() => import('@/components/WorldMap'), { ssr: false });

interface OutletMapSectionProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes: string[];
    source_count: number;
  }>;
}

export default function OutletMapSection({ centroids }: OutletMapSectionProps) {
  return <WorldMap centroids={centroids} />;
}
